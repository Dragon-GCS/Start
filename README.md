# Start

A python package manager based on pip and venv, use `pyproject.toml` instead of `requirements.txt`

## install

Install from github

```bash
>>> git clone https://github.com/dragon-gcs/start
>>> cd start
>>> pip install .
```

> `start` is a default alias in **powershell**, so use **`Remove-Item alias:start -Force`** to remove alias before use `start`
> **Optional:** Add `Remove-Item alias:start -Force` in powershell profile

## Usage

- `start init` Init current folder
- `start new <project name>`新建项目，创建**README.md**、**setup.py**、**pyproject.toml**、**<project_name>/**、**test/** 等相关文件和目录
- `start install/add` 安装包并添加到依赖中
- `start remove/rm` 从依赖和硬盘中移除包
