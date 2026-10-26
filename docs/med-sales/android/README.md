# medapp · 医药销售 Android 客户端

> [观看移动端演示视频](https://www.bilibili.com/video/BV1WtnQ6BE7F/) ·
> [下载 APK（GitHub Release 26.10.1）](https://github.com/dfxiang/med-sales/releases/download/26.10.1/medsales-release-unsigned-26.10.26.1.apk)
>
> Release 文件为 `medsales-release-unsigned-26.10.26.1.apk`，当前未签名；正式分发前请使用自己的证书签名。

`medapp` 是 med-sales 的移动销售工作台，沿用仓库参考项目的轻量框架：

```text
WebView（APK 内置 www 资源）
  ├─ GET  /api/**  → AppWebViewClient → OkHttp → FastAPI
  └─ 写请求         → NativeBridge    → OkHttp → FastAPI
```

这样页面始终从 APK 本地加载，不依赖浏览器安全上下文；GET 接口与页面同源，
带请求体的登录、发货、取消、资料修改等操作通过原生桥执行，不需要 CORS。

## 功能

- 支持的平台：Android 8.0（API 26）及以上，目标 Android 15（API 35）。
- 登录与权限：JWT 登录、按 `/auth/me` 权限显示导航和写操作。
- 经营首页：最近月销售、环比、库存不足、待处理退货、应收与 GSP 风险、
  近六月趋势和最近订单。
- 销售订单：服务端分页、订单号片段搜索、状态/客户筛选、订单详情、新建订单、
  发货和取消。
- 库存查询：按商品/仓库/状态筛选，展示库存与安全库存、分页。
- GSP 合规：证照与批次到期统计、90 天窗口分级和预警列表。
- 我的：个人资料、修改密码、刷新权限、切换服务器、退出登录。

列表分页沿用仓库约定：每页 `10 / 20 / 50 / 100`，默认 `20`，切页位于底部，
筛选变化后回到第 1 页；数据均来自服务端 `page / size / total`。

## 目录

```text
android/
├── app/src/main/java/com/danny/medapp/
│   ├── MainActivity.kt          # WebView 宿主、边到边、系统返回
│   ├── net/                     # 可配置服务器地址、OkHttp 请求
│   └── web/                     # GET 代理、原生桥、路由与 JSON
├── app/src/main/assets/www/     # 离线打包的移动界面
├── app/src/test/                # JVM 单元测试
└── README.md
```

## 环境与构建

要求 JDK 17、Android SDK Platform 35、Build-Tools 35.0.0。

```bash
cd android
printf 'sdk.dir=%s\n' "$ANDROID_HOME" > local.properties
./gradlew testDebugUnitTest
./gradlew assembleDebug
```

APK 输出：`app/build/outputs/apk/debug/app-debug.apk`。

安装到已连接设备：

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

包名 `com.danny.medapp`，应用名 `medapp`，最低 Android 8.0（API 26），
目标 Android 15（API 35）。

## 后端地址

- 默认：`http://10.0.2.2:8001`，适用于 Android Studio 模拟器访问宿主机。
- 真机：打开登录页“服务器地址”，或在“我的 → 服务器地址”中填写电脑的局域网地址，
  例如 `http://192.168.1.10:8001`。手机和电脑必须处于同一网络，并允许 8001 端口访问。
- 生产：建议使用 HTTPS，并同步把
  `app/src/main/res/xml/network_security_config.xml` 的明文流量改为关闭。

服务器地址保存在本机 `SharedPreferences`，切换服务器后会清除当前登录令牌并要求重新登录。

## 移动界面验证

在运行中的 8001 后端上，运行打包前移动界面回归：

```bash
cd frontend
npx playwright test --config playwright.android.config.ts
```

该套件使用 Pixel 7 视口直接加载 `android/app/src/main/assets/www`，覆盖真实登录、
首页、销售分页/搜索/客户选择、库存、GSP 和个人页，并检查手机宽度下无横向溢出。

## 安全说明

- WebView 禁用文件访问、内容访问、缩放和混合内容。
- GET 代理只允许 `/api/**`；写请求桥只允许 `POST / PUT / PATCH / DELETE /api/**`。
- 生产部署应使用 HTTPS；若继续使用 HTTP，请只在可信局域网内运行，并收紧
  `network_security_config.xml`。
- Release 产物默认未签名，分发前需配置自己的签名证书。
