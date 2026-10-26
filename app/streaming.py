"""流式合成的后台执行与断线处理。

为什么需要这一层：

Starlette 在客户端断开连接时，是通过「取消响应任务」来停止发送的。
如果响应体是一个同步生成器（``StreamingResponse`` 会把它放进线程池里迭代），
被取消时这个生成器不会执行 ``finally``——它会一直挂在 yield 处，
连同它内部持有的推理锁一起被丢弃，直到垃圾回收才恢复。
表现就是：网页点了「停止」之后，服务在几十秒内对任何合成请求都不响应。

因此流式合成统一放到独立线程（``GeneratorWorker``）里执行：

* worker 线程持有生成器与推理锁，正常结束或被取消时都一定会 ``close()`` 生成器；
* 取消信号有两个来源：客户端断开（由 ``DisconnectTrackingMiddleware`` 转成
  ``threading.Event``），以及消费端主动 ``close()``；
* 消费端（HTTP 响应体）即使被直接丢弃也不影响正确性，最坏情况只是多算一小段。
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Any, Callable, Iterable, Iterator, Optional


LOGGER = logging.getLogger(__name__)

#: 消费端收到它表示事件流结束
SESSION_DONE = object()

_DISCONNECT_SCOPE_KEY = "moss_tts_disconnect_event"


class DisconnectTrackingMiddleware:
    """纯 ASGI 中间件：把 ``http.disconnect`` 变成一个线程可观测的 Event。

    消息仍会原样转发给内层应用，所以 Starlette 自身的断线处理不受影响。
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        disconnect_event = threading.Event()
        scope[_DISCONNECT_SCOPE_KEY] = disconnect_event

        async def wrapped_receive():
            message = await receive()
            if message.get("type") == "http.disconnect":
                disconnect_event.set()
            return message

        await self.app(scope, wrapped_receive, send)


def disconnect_event_for(scope: dict[str, Any]) -> Optional[threading.Event]:
    event = scope.get(_DISCONNECT_SCOPE_KEY)
    return event if isinstance(event, threading.Event) else None


class GeneratorWorker:
    """在后台线程里迭代生成器，并把事件放进有界队列供消费端读取。"""

    def __init__(
        self,
        factory: Callable[[], Iterator[dict[str, Any]]],
        *,
        cancels: Iterable[Optional[threading.Event]] = (),
        queue_size: int = 32,
        name: str = "moss-tts-stream",
    ) -> None:
        self._factory = factory
        self._stop = threading.Event()
        self._cancels: tuple[threading.Event, ...] = tuple(
            event for event in (*cancels, self._stop) if event is not None
        )
        self._queue: "queue.Queue[Any]" = queue.Queue(maxsize=max(1, int(queue_size)))
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._error: Optional[BaseException] = None

    # -------------------------------------------------------------- 生命周期

    def start(self) -> "GeneratorWorker":
        self._thread.start()
        return self

    def close(self) -> None:
        """请求取消并等待 worker 退出（生成器一定会在 worker 里被关闭）。"""
        self._stop.set()
        self._thread.join(timeout=10.0)

    @property
    def error(self) -> Optional[BaseException]:
        return self._error

    # ---------------------------------------------------------------- 内部执行

    def _cancelled(self) -> bool:
        return any(event.is_set() for event in self._cancels)

    def _run(self) -> None:
        generator: Optional[Iterator[dict[str, Any]]] = None
        try:
            generator = self._factory()
            for event in generator:
                if self._cancelled():
                    break
                while not self._cancelled():
                    try:
                        self._queue.put(event, timeout=0.2)
                        break
                    except queue.Full:
                        continue
        except BaseException as exc:  # noqa: BLE001 - 需要把错误透给消费端
            self._error = exc
            LOGGER.exception("stream worker failed")
        finally:
            if generator is not None:
                try:
                    generator.close()
                except Exception:  # pragma: no cover
                    LOGGER.debug("failed to close stream generator", exc_info=True)
            # 队列可能已满：丢几条过期数据给结束哨兵腾位置
            while True:
                try:
                    self._queue.put(SESSION_DONE, timeout=0.2)
                    break
                except queue.Full:
                    try:
                        self._queue.get_nowait()
                    except queue.Empty:  # pragma: no cover
                        pass

    # ------------------------------------------------------------------ 消费端

    def next_event(self, timeout: float = 0.5) -> Any:
        """取下一个事件；超时返回 ``None``；结束时返回 ``SESSION_DONE``。"""
        try:
            item = self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
        if item is SESSION_DONE:
            if self._error is not None:
                raise self._error
            return SESSION_DONE
        return item
