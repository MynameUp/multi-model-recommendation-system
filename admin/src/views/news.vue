<template>
    <div style="padding: 10px">
        <div style="background: #fff; border-radius: 8px; padding: 20px;">
            <div class="query-c">
                查询：
                <!-- 💡 换行处理，防止单行过长 -->
                <Input
                    v-model="keyword"
                    @on-change="searchNews"
                    search
                    placeholder="标题/新闻内容检索"
                    style="width: auto" />
            </div>
            <br/>
            <div>
                <!-- 💡 换行处理 -->
                <Table
                    :height="tableHeight"
                    border
                    stripe
                    :columns="columns1"
                    :data="nowData"
                    size="small"
                    @mouseup="longText">
                </Table>
                <br/>
                <div class="pageBox" v-if="data1.length" >
                    <Page :total="parseInt(totalPage)"
                          :page-size="pageSize"
                          :page-size-opts="[10 ,20 ,30]"
                          show-elevator
                          show-total
                          show-sizer
                          @on-change="changepage"
                          @on-page-size-change="nowPageSize">
                    </Page>
                    <p>总共{{dataCount}}页</p>
                </div>
                <Drawer :closable="false" width="640" v-model="value3">
                    <h2 :style="pStyle">新闻详情</h2>
                    <p :style="pStyle">基本信息</p>
                    <div :model="news">
                        <div class="demo-drawer-profile">
                            <Row>
                                <Col span="24">
                                    <h5>标题:</h5> {{ news.title }}
                                </Col>
                            </Row>
                            <Divider />
                            <Row>
                                <Col span="12">
                                    <h5>发表日期:</h5> {{ news.date }}
                                </Col>
                                <Col span="12">
                                    <h5>类别:</h5> {{ news.category }}
                                </Col>
                            </Row>
                            <Divider />
                            <Row>
                                <Col span="24">
                                    <h5>原链接:</h5>
                                    <a :href="news.url" target="_blank">{{ news.url || '暂无原始链接' }}</a>
                                </Col>
                            </Row>
                        </div>
                        <Divider />

                        <!-- 💡 新增：正文内容显示区块 -->
                        <p :style="pStyle">正文内容</p>
                        <div class="demo-drawer-profile">
                            <Row>
                                <Col span="24">
                                    <!-- 💡 这里的超长代码已经被完美折行 -->
                                    <div
                                        v-html="news.mainpage || '暂无正文内容'"
                                        style="line-height: 1.6; font-size: 14px; text-indent: 2em;">
                                    </div>
                                </Col>
                            </Row>
                        </div>
                        <Divider />

                        <p :style="pStyle">图片素材</p>
                        <div class="demo-drawer-profile">
                            <Row>
                                <Col span="24">
                                    <p v-for="(item,index) in news.pic_url" :key="index">
                                        <a :href="item" target="_blank">{{item}}</a><br>
                                        <!-- 💡 图片标签也进行了折行 -->
                                        <img
                                            :src="item"
                                            style="max-width: 100%; margin-top: 10px; border-radius: 4px;"
                                            v-if="item">
                                    </p>
                                    <span v-if="!news.pic_url || news.pic_url.length === 0">暂无图片</span>
                                </Col>
                            </Row>
                        </div>
                        <Divider />
                        <p :style="pStyle">视频素材</p>
                        <div class="demo-drawer-profile">
                        <Row>
                            <Col span="24">
                               {{ news.videourl || '暂无视频' }}
                            </Col>
                        </Row>
                    </div>
                    </div>
                </Drawer>
                <Modal
                    v-model="modal1"
                    title="确认中......."
                    @on-ok="delok"
                    @on-cancel="delcancel">
                    <h3>确认删除当前新闻吗？？</h3>
                </Modal>
            </div>
        </div>
    </div>
</template>

<script>
import { fetchNewsData, delNewsData, getSearchNewsResult } from '@/api'

export default {
    name: 'newslist',
    inject: ['reload'],
    mounted() {
        window.onresize = () => {
            this.screenHeight = document.body.clientHeight
            this.tableHeight = this.screenHeight - 300
        }
    },
    data() {
        return {
            keyword: '',
            tableHeight: window.innerHeight - 250,
            screenHeight: document.body.clientHeight,
            delnewsurl: '',
            modal1: false,
            pStyle: {
                fontSize: '16px', color: 'rgba(0,0,0,0.85)', lineHeight: '24px', display: 'block', marginBottom: '16px',
            },
            news: {
                title: '', url: '', date: '', category: '', pic_url: [], videourl: '', mainpage: '',
            },
            value3: false,
            totalPage: 0,
            pageSize: 10,
            dataCount: 0,
            pageCurrent: 1,
            nowData: [],
            columns1: [
                {
                    title: '标题',
                    key: 'title',
                    align: 'center',
                    render: (h, params) => {
                        let texts = params.row.title || '无标题'
                        if (texts.length > 9) texts = texts.slice(0, 8) + '...'
                        return h('div', [
                            h('Tooltip', { props: { placement: 'top', transfer: true } }, [
                                texts,
                                h('span', { slot: 'content', style: { whiteSpace: 'normal' } }, params.row.title),
                            ]),
                        ])
                    },
                },
                { title: '发布日期', key: 'date', align: 'center' },
                {
                    title: '原始链接',
                    key: 'url',
                    align: 'center',
                    render: (h, params) => {
                        let texts = params.row.url || '暂无链接'
                        if (texts.length > 15) texts = texts.slice(0, 15) + '...'
                        return h('div', [
                            h('Tooltip', { props: { placement: 'top', transfer: true } }, [
                                texts,
                                h('span', { slot: 'content', style: { whiteSpace: 'normal', wordBreak: 'break-all' } }, params.row.url),
                            ]),
                        ])
                    },
                },
                {
                    title: '类别',
                    key: 'category',
                    align: 'center',
                    filters: [{ label: '国内', value: '国内' }, { label: '财经', value: '财经' }],
                    filterMultiple: false,
                    filterMethod(value, row) { return row.category === value },
                },
                { title: '评论量', key: 'comments', align: 'center' },
                { title: '阅读量', key: 'readnum', align: 'center' },
                {
                    title: '操作',
                    key: 'action',
                    width: 150,
                    align: 'center',
                    render: (h, params) => h('div', [
                        h('Button', {
                            props: { type: 'primary', size: 'small' },
                            style: { marginRight: '5px' },
                            on: {
                                click: () => {
                                    let picList = []
                                    if (params.row.pic_url && params.row.pic_url !== '[]' && params.row.pic_url !== 'None') {
                                        try {
                                            let cleanStr = String(params.row.pic_url).replace(/'/g, '"')
                                            let parsed = JSON.parse(cleanStr)
                                            picList = Array.isArray(parsed) ? parsed : [parsed]
                                        } catch (e) {
                                            picList = [params.row.pic_url]
                                        }
                                    }

                                    this.news.videourl = (params.row.videourl === 'None' || !params.row.videourl) ? '' : params.row.videourl
                                    this.news.title = params.row.title
                                    this.news.date = params.row.date
                                    this.news.pic_url = picList
                                    this.news.url = params.row.url
                                    this.news.mainpage = params.row.mainpage
                                    this.news.category = params.row.category
                                    this.value3 = true
                                },
                            },
                        }, '详情'),
                        h('Button', {
                            props: { type: 'error', size: 'small' },
                            on: {
                                click: () => {
                                    this.modal1 = true
                                    this.delnewsurl = params.row.url || params.row.newsid
                                },
                            },
                        }, '删除'),
                    ]),
                },
            ],
            data1: [],
        }
    },
    methods: {
        formatNewsData(rawList) {
            const categoryMap = ['美股', '国内', '国际', '社会', '体育', '娱乐', '军事', '科技', '财经', '股市', '全部']
            let a = []
            for (let i = 0; i < rawList.length; i++) {
                let item = rawList[i]
                let fields = item.fields ? item.fields : item

                let dict = {}
                dict.newsid = item.news_id || item.pk
                dict.title = fields.title
                dict.date = fields.date
                dict.mainpage = fields.mainpage
                dict.pic_url = fields.pic_url
                dict.videourl = fields.videourl
                dict.category = categoryMap[fields.category] || '未知'
                dict.readnum = fields.readnum || 0
                dict.url = fields.url || fields.origin_url
                dict.comments = fields.comments || 0
                a.push(dict)
            }
            return a
        },
        searchNews() {
            getSearchNewsResult(this.keyword).then(res => {
                let listjson = typeof res.newslist === 'string' ? JSON.parse(res.newslist) : (res.newslist || [])
                this.totalPage = listjson.length
                this.dataCount = Math.ceil(listjson.length / this.pageSize)

                this.data1 = this.formatNewsData(listjson)
                this.changepage(1)
            })
        },
        delok() {
            delNewsData(this.delnewsurl).then(res => {
                if (res.message === 'Success.') {
                    this.$Message.info('删除成功')
                    this.reload()
                } else {
                    this.$Message.info('出错！请重试！')
                }
            })
        },
        delcancel() {
            this.$Message.info('取消')
        },
        longText(item) {
            return item
        },
        changepage(index) {
            let startIdx = (index - 1) * this.pageSize
            let endIdx = index * this.pageSize
            this.nowData = this.data1.slice(startIdx, endIdx)
            this.pageCurrent = index
        },
        nowPageSize(index) {
            this.pageSize = index
            this.changepage(1)
        },
    },
    created() {
        fetchNewsData().then(res => {
            let listjson = typeof res.newslist === 'string' ? JSON.parse(res.newslist) : (res.newslist || [])
            this.totalPage = listjson.length
            this.dataCount = Math.ceil(listjson.length / this.pageSize)

            this.data1 = this.formatNewsData(listjson)
            this.changepage(1)
        }).catch(err => {
            console.error('加载管理员新闻数据失败:', err)
            this.$Message.error('加载数据失败')
        })
    },
}
</script>

<style scoped>
</style>