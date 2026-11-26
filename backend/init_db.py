import argparse
import sys

from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from app import app, init_db
from config import Config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-mysql', action='store_true')
    args = parser.parse_args()
    url = make_url(Config.SQLALCHEMY_DATABASE_URI)
    if args.require_mysql and url.get_backend_name() != 'mysql':
        parser.error('请在 backend/.env 的 DATABASE_URL 中配置目标 MySQL 实例和数据库名。')
    print(f'数据库类型: {url.get_backend_name()}，目标库: {url.database}')

    try:
        init_db()
    except OperationalError as error:
        code = error.orig.args[0] if error.orig.args else None
        hints = {
            1044: '数据库账号无权访问或创建目标库。请管理员建库并向应用账号授予该库权限。',
            1045: 'MySQL 拒绝认证。请检查 DATABASE_URL 中的账号、密码及允许连接的主机。',
            1049: '目标数据库不存在。请管理员核对实例、端口和库名，并创建目标库。',
            2003: '无法连接 MySQL。请核对服务是否运行，以及 DATABASE_URL 的主机和端口。',
        }
        sys.exit(hints.get(code, '数据库初始化失败，请检查数据库连接和服务日志。'))

    print('数据库初始化完成。')


if __name__ == '__main__':
    main()
