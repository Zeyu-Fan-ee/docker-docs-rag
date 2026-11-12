# Docker 本机运行指南

## 已完成的部署

项目在 Docker Desktop 的 WSL 2 引擎中运行：`api` 提供检索和问答接口，`ui` 提供 Streamlit 页面。两者通过 Docker Compose 管理，页面通过容器网络访问 API，对外只开放本机端口。

- 页面：http://127.0.0.1:8501
- 后端健康检查：http://127.0.0.1:8000/health
- 项目目录：`D:\AI\RAG`
- Docker Desktop 程序：`D:\Docker\Desktop`
- Docker 主要数据磁盘：`D:\Docker\WSL\disk\docker_data.vhdx`
- 容器内独立知识库：1036 个片段，保存在 `rag-runtime` 数据卷；模型缓存保存在 `model-cache` 数据卷。

Docker 的部分设置、日志和 Windows 系统组件仍可能位于系统盘。此部署为本机演示，不是公网或企业生产部署。

## 日常启动

1. 启动 Docker Desktop，等待左下角显示 **Engine running**。
2. 打开 PowerShell，执行：

```powershell
cd D:\AI\RAG
docker compose up -d
docker compose ps
```

3. 打开 http://127.0.0.1:8501 提问。首次加载模型可能较慢，也可能需要下载未缓存的模型。

## 停止和再次使用

```powershell
cd D:\AI\RAG
docker compose stop
```

这会停止容器，保留镜像和数据卷。下次运行 `docker compose up -d` 即可再次启动；不需要重新建库。关闭网页不会停止容器，退出 Docker Desktop 则会停止 Docker 引擎。当前配置没有设置容器自动重启。

不要使用 `docker compose down -v`，该命令会删除项目数据卷，包括容器知识库和模型缓存。

## 排查

- 页面打不开：先确认 Docker Desktop 显示 Engine running，再执行 `docker compose ps` 查看两个服务是否运行，确认端口 8501 没有被占用。
- API 未就绪：执行 `docker compose logs --tail 50 api` 查看日志，或访问健康检查地址；前端会等待后端通过健康检查。
- 答案无法生成：检查项目 `.env` 中模型配置和 API 密钥、余额及网络；不要把密钥发给别人或提交到 Git。
- 需要看前端日志：执行 `docker compose logs --tail 50 ui`。
- 容器数据库和本机原数据库是独立的。不要为了日常启动重复运行 `build_db.py`；它会创建知识库，并可能覆盖指定目录下的构建记录。

## 面试时怎么解释

使用 Dockerfile 描述 Python 运行环境和依赖，构建项目镜像；使用 Docker Compose 协调 FastAPI 后端和 Streamlit 前端，通过健康检查控制启动顺序，并用命名数据卷持久化向量库和模型缓存。这样可以用统一方式在本机启动项目，减少环境配置差异。实际验证包括容器健康检查、页面访问，以及人工提问收到回答。
