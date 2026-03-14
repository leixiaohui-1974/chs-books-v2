# CHS-Books-v2 同步命令速查

## 1. 推送到 GitHub
```bash
cd "D:\cowork\教材\chs-books-v2"
git -c http.proxy= push origin main
```

## 2. 同步到学校服务器 (27.188.73.166:4422, user=lei, pwd=lei)
```bash
# 打包
cd "D:/cowork/教材/chs-books-v2"
tar czf /tmp/chs-full.tar.gz --exclude='.git' --exclude='archive' T1-CN T2a T2b T3-Engineering

# 传输 + 解压
scp -P 4422 /tmp/chs-full.tar.gz lei@27.188.73.166:/home/lei/chs-full.tar.gz
ssh -p 4422 lei@27.188.73.166 "cd /home/lei/chs-books-v2 && tar xzf /home/lei/chs-full.tar.gz && rm /home/lei/chs-full.tar.gz"
```

## 注意事项
- GitHub: 用 `http.proxy=` 直连，不走SOCKS5代理
- 学校服务器: 无git仓库，用SCP+tar同步；无rsync
- 连接信息来源: `D:\cowork\个人\27.188.73.166.txt`
- 最后同步: 2026-03-13, commit 4a39027
