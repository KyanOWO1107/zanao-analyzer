# 赞噢抓包样本分析

样本来源：本地 `@private/` 目录。该目录已在 `.gitignore` 中忽略，不应提交。

## 总结

抓包中存在两套入口：

- App：`http://api.app.zanao.com`
- 小程序：`https://api.x.zanao.com`

两套接口的数据结构非常接近。对当前项目而言，小程序路径更接近参考项目，且已经覆盖校内列表、详情、评论三类接口。

小程序响应“看不出来”的原因不是业务加密，而是抓包文件中保留了 HTTP 的 `Transfer-Encoding: chunked` 与 `Content-Encoding: gzip` 原始正文。需要先解 chunk，再 gzip 解压，之后就是正常 JSON。

## App 与小程序差异

### 帖子列表

App：

```text
GET http://api.app.zanao.com/thread/v2/list
query: cate_id, from_time, with_comment, with_reply
```

小程序：

```text
POST https://api.x.zanao.com/thread/v2/list
form: cate_id, from_time, with_comment, with_reply
```

列表响应均包含：

```text
data.list
data.user_cert_valid
data.cert_show_open
data.tag_show
```

列表项字段高度一致，常用字段：

```text
thread_id
title
content
nickname
p_time
post_time
cate_id
cate_name
view_count
c_count
l_count
comment_list
sign
```

App 列表项额外出现：

```text
from_app
```

### 帖子详情

App：

```text
POST http://api.app.zanao.com/thread/info
form: id, from
```

小程序：

```text
POST https://api.x.zanao.com/thread/info
form: id
```

详情响应均包含：

```text
data.detail
data.t_sign
data.report_type_map
data.top_conf
data.cert_valid
data.comment_cert_valid
```

`data.detail` 常用字段：

```text
thread_id
title
content
contact_phone
contact_qq
contact_wx
view_count
mark_num
like_num
dislike_num
post_time
pt_time
cate_name
nickname
headimgurl
short_url
sign
```

App 的 `data.detail` 额外出现：

```text
from_app
```

小程序详情响应的 `data` 额外出现：

```text
banner_list
```

### 评论列表

App：

```text
GET http://api.app.zanao.com/comment/list
query: id, sign, with_hongbao
```

小程序：

```text
POST https://api.x.zanao.com/comment/list
form: id, sign, with_hongbao
```

评论响应结构一致：

```text
data.list
data.total
data.user_cert_valid
data.cert_show_open
data.author_like_open
data.delete_open
```

## 鉴权和请求头差异

App 使用：

```text
X-Sc-Token
X-Sc-Client: app
X-Sc-Platform: Android
X-Sc-Device
X-Sc-Version
X-Sc-Alias
X-Sc-Nd
X-Sc-Td
X-Sc-Ah
```

小程序使用：

```text
X-Sc-Od
X-Sc-Appid
X-Sc-Platform
X-Sc-Cloud
X-Sc-Nwt
X-Sc-Version
X-Sc-Alias
X-Sc-Wf
X-Sc-Nd
X-Sc-Td
X-Sc-Ah
xweb_xhr
Referer
User-Agent
```

共同点：

- `X-Sc-Alias` 是学校 alias。
- `X-Sc-Nd`、`X-Sc-Td`、`X-Sc-Ah` 是动态字段。
- `X-Sc-Ah` 长度 32，表现为 MD5 十六进制摘要。

## 推荐实现路线

当前只做本校校内监测，因此推荐优先实现小程序客户端：

```text
POST https://api.x.zanao.com/thread/v2/list
POST https://api.x.zanao.com/thread/info
POST https://api.x.zanao.com/comment/list
```

第一小步只实现列表 dry-run：

```text
读取 .env
生成 X-Sc-Nd / X-Sc-Td / X-Sc-Ah
POST /thread/v2/list
解析 data.list
输出脱敏后的前 N 条帖子
```

暂不实现：

- App 端接口
- 跨校接口
- 评论采集
- 高频轮询

## 已确认事项

- `X-Sc-Ah` 的生成方式与参考项目一致：

```text
md5("{alias}_{nd}_{td}_{api_salt}")
```

- 已用本地小程序抓包样本中的 4 个请求验证候选 salt，全部能复现抓包里的 `X-Sc-Ah`。
- 本地 `.env` 已补齐 `ZANAO_API_SALT`，该文件被 Git 忽略。

## 未确认事项

- token 的有效期和失效表现。

## 当前 dry-run 结果

- 已使用当前 `.env` 请求小程序 `/thread/v2/list`。
- `python -m zanao_monitor.cli fetch-mini-list --limit 3` 成功返回 3 条校内帖子。
- 该命令目前只打印列表，不入库、不推送。
- `python -m zanao_monitor.cli fetch-mini-list --limit 20 --match` 可预览规则命中结果；预览模式不写去重状态。
