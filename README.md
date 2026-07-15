# 彩華摄影档案 · 云端回传建档部署说明

本目录是一套**纯前端 + 单文件 Python 服务器**的摄影工作流系统：
- `booking.html`：发给客户的预约问卷（填完直接回传到服务器）
- `index.html`：你的档案管理站（待办预约、一键建档、进度条、价格、选图加单…）
- `server.py`：本地/云端服务器（仅用 Python 标准库，零依赖）

本文档说明如何把 `server.py` 部署到云端，**让客户在外面填完表单就能直接回传到你的档案站**。

---

## 整体原理（一分钟看懂）

```
客户手机打开预约链接
      ↓  填写并提交
云端 server.py（收件箱，只存预约 JSON）
      ↓  你本地的档案站带 ?api=云端地址 打开
待办预约自动出现 → 一键建档 → 照片仍留你本地
```

- 照片/原图**永远只存在你本地电脑**，不会上传云端（隐私 + 省流量）。
- 云端只当"收件箱"：接收客户提交的预约表单，等你来取。
- 取到后本地建档，云端那条预约自动删除。

---

## 步骤一：把代码推到 GitHub

> 你已经在用 GitHub 了，这一步是把文件夹变成一个仓库并推上去。

在终端（项目目录 `photography-manager` 下）依次执行：

```bash
# 1. 初始化仓库（只需第一次）
git init

# 2. 纳入全部文件
git add .

# 3. 提交
git commit -m "彩華摄影档案：预约回传 + 档案管理"

# 4. 关联到你在 GitHub 上新建的仓库（把 URL 换成你自己的）
git remote add origin https://github.com/你的用户名/saika-booking.git

# 5. 推送到 GitHub
git push -u origin main
```

> ⚠️ 第 4 步的仓库需要你先在 GitHub 网页上点 **New repository** 新建一个
> （名字随意，例如 `saika-booking`，**不要**勾选自动生成 README，保持空仓库）。
> 新建后页面会显示仓库地址，复制 `https://github.com/你的用户名/仓库名.git` 填进去即可。

---

## 步骤二：部署到 Render（免费，常驻云端收件箱）

1. 打开 https://render.com ，用 **GitHub 账号登录**。
2. 点 **New + → Blueprints**（或直接 New Web Service）。
3. 授权 Render 访问你的 GitHub，选择刚推上去的仓库。
4. Render 会自动读到本目录的 `render.yaml`，直接点 **Apply / Deploy**。
5. 等 1～2 分钟，状态变绿后，Render 会给你一个地址，形如：
   ```
   https://saika-booking.onrender.com
   ```
   这就是你的**云端收件箱地址**，复制它备用。

（若用 New Web Service 而非 Blueprints：Runtime 选 Python，Build Command 填
`pip install -r requirements.txt`，Start Command 填 `python3 server.py` 即可。）

---

## 步骤三：给客户发新的预约链接

把云端地址拼到现有的公网预约表单后面，例如：

```
https://1d69b7f31f5149d1abfa37167964ce03.app.codebuddy.work/?api=https://saika-booking.onrender.com
```

客户在这个链接里填完提交 → 表单直接回传到你的云端收件箱。

> 你可以把这个带 `?api=` 的链接设为书签 / 发给客妹，原来的不带 `?api=` 的链接
> 仍可用（只是提交走本地）。

---

## 步骤四：你这边打开带云端地址的档案站

在你自己的电脑上，用带 `?api=` 的地址打开档案管理站：

```
http://localhost:8765/index.html?api=https://saika-booking.onrender.com
```

（需本机 `server.py` 在运行：终端执行 `python3 server.py`）

打开后：
- 顶部「⏰ 待处理预约」会自动出现客户刚提交的预约；
- 每条显示**预计总价/定金/尾款**；
- 点「💰 确认价格并建档」→ 自动生成档案（照片留在本地）；
- 建档后该待办自动从云端删除。

---

## 注意事项

- **Render 免费实例会休眠**：超过约 15 分钟无访问会睡，第一次打开要等
  30～50 秒冷启动，属正常现象。
- **云端磁盘是临时的**：免费实例重部署后磁盘会重置。本系统把云端当"临时收件箱"，
  预约取出建档后即删除，所以不影响使用。若想长期留存云端备份，可升级付费实例
  或改用 Railway（带持久磁盘）。
- 价格、加单、进度条等所有业务设置都在你**本地**的档案管理站「设置」里改，
  与云端无关。
- 本地电脑未开机时，客户提交的预约会暂存在云端，等你开机打开档案站再来取。

---

## 本地日常使用（不需要云端也能跑）

```bash
cd photography-manager
python3 server.py
# 浏览器打开 http://localhost:8765/index.html
```

本地模式下，客户需用 `http://localhost:8765/booking.html` 提交（同一台电脑）才会进档案站；
要"外面也能回传"就必须走上面的云端步骤。
