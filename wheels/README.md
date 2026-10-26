# 本地离线 wheel

如果容器内下载 Python 依赖很慢，可以先在浏览器或网络更快的机器上下载
`.whl` 文件，放到本目录，再构建镜像。

`Dockerfile` 和 `Dockerfile.gpu` 都会把本目录只读挂载到构建阶段的 `/wheels`，
校验并按文件路径直接安装这里的**所有** `.whl`（`torch` / `torchaudio` 除外），
wheel 不会进入最终镜像。损坏或下载了一半的文件会直接报出文件名。
缺少的依赖仍会从
`PIP_INDEX_URL` 指定的 PyPI 镜像下载。

GPU 基础镜像使用 Python 3.12 / x86_64。最耗时的是 `pynini==2.1.7`
（约 166MB），匹配的 wheel 文件名通常为：

```text
pynini-2.1.7-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl
```

可以在浏览器打开以下任一页面，搜索上面的文件名下载：

- <https://pypi.tuna.tsinghua.edu.cn/simple/pynini/>
- <https://mirrors.aliyun.com/pypi/simple/pynini/>

清华镜像的直链：

```text
https://pypi.tuna.tsinghua.edu.cn/packages/ef/16/8624f73412f4571517dc97e027c6b73db849c7c649aad70aa2dd168834a1/pynini-2.1.7-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl
```

可以在能访问 PyPI 的机器上一次下载全部运行依赖：

```bash
python -m pip download --only-binary=:all: \
  --dest wheels -r requirements.txt
```

也可以只把浏览器下载的 `pynini` wheel 放进本目录，其余小文件让容器下载。
