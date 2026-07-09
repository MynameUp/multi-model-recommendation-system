<template>
    <div style="background:#eee; width: 100%; height: 100%; overflow: scroll;">
        <Row>
            <Col span="8">
                <div style="background:#eee;padding: 20px;" :style="styObj">
                    <Card :bordered="false">
                        <h3 slot="title">URL采集配置</h3>
                        <span>
                                <span style="margin-left: 5px; font-size: larger;">时间间隔</span>
                                <span style="float: right;">
                                    <TimePicker v-model="urltime" :steps="[1, 1, 1]" placeholder="Time"
                                                style="width: 112px"></TimePicker>
                                </span>
                                <br/><br/><br/>
                                <span style="margin-left: 5px; font-size: larger;">启动爬虫</span>
                                <span style="float: right;">
                                    <i-switch v-model="urlstate" @click.native="BeginUrlSpider"/></span>
                            </span>
                    </Card>
                    <Card :bordered="false" style="margin-top: 20px;">
                        <h3 slot="title">新闻详情采集配置</h3>
                        <span>
                                <span style="margin-left: 5px; font-size: larger;">时间间隔</span>
                                <span style="float: right;">
                                    <TimePicker v-model="detailtime" :steps="[1, 1, 1]"
                                                placeholder="Time" style="width: 112px"></TimePicker>
                                </span>
                                <br/><br/><br/>
                                <span style="margin-left: 5px; font-size: larger;">启动爬虫</span>
                                <span style="float: right;">
                                    <i-switch v-model="detailstate" @click.native="BeginDetailSpider"/></span>
                            </span>
                    </Card>
                    <Card :bordered="false" style="margin-top: 20px;">
                        <h3 slot="title">运行情况</h3>
                        <ChartLint ref="chart_line_one" style="display: inline-block;"></ChartLint>
                    </Card>
                </div>
            </Col>
            <Col span="16">
                <div style="background:#eee;padding: 20px; " :style="styObj">
                    <Card :bordered="false">
                        <h3 slot="title">URL采集日志</h3>
                        <Table height="200"
                               :columns="UrlColumns" :data="UrlData" @on-row-click="downloadLog"></Table>
                    </Card>
                    <Card :bordered="false" style="margin-top: 10px;">
                        <h3 slot="title">详情采集日志</h3>
                        <Table height="200" :columns="DetailColumns" :data="DetailData"
                               @on-row-click="downloadLog"></Table>
                    </Card>
                    <Card :bordered="false" style="margin-top: 10px;">
                        <h3 slot="title">注意事项</h3>
                        <Collapse height="200">
                            <Panel name="1">
                                重启爬虫
                                <p slot="content">爬虫重启为强制性重启，该操作可能会造成之前采集未来得及存入数据库的内容丢失请注意！尽量在空闲时使用该功能，避免数据丢失</p>
                            </Panel>
                            <Panel name="2">
                                关闭爬虫
                                <p slot="content">关闭爬虫意味着近期将无法获取到最新的新闻内容，请酌情使用该功能</p>
                            </Panel>
                        </Collapse>
                    </Card>
                </div>
            </Col>
        </Row>
    </div>
</template>

<script>
// 1. 先导入别名模块
import {
    urlspider,
    getSpiderPageData,
    closeurlspider,
    closedetailspider,
    detailspider,
} from '@/api'
// 2. 后导入相对路径模块
import ChartLint from '../components/SpiderChartLint'

// [修复] 此处必须保留一个空行
export default {
    components: { ChartLint },
    name: 'Spider',
    data() {
        return {
            urlstate: false,
            detailstate: false,
            urltime: '',
            detailtime: '',
            name: '新闻采集量',
            xData: [],
            yData: [],
            UrlColumns: [
                { title: '日志文件名', key: 'name' },
                { title: '时间', key: 'date' }, // [修复] 末尾补逗号
            ],
            UrlData: [],
            DetailColumns: [
                { title: '日志文件名', key: 'name' },
                { title: '时间', key: 'date' }, // [修复] 末尾补逗号
            ],
            DetailData: [],
            styObj: { height: '0px' }, // [修复] 末尾补逗号
            screenHeight: 0,
            tableHeight: 0,
        }
    },
    mounted() {
        this.$refs.chart_line_one.initChart(this.name, this.xData, this.yData)
        window.addEventListener('resize', this.handleResize)
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.handleResize)
        window.removeEventListener('resize', this.changeHeight)
    },
    methods: {
        parseTimeToSeconds(timeStr) {
            if (!timeStr) return 0
            const temp = timeStr.split(':')
            if (temp.length !== 3) return 0
            return Number(temp[0]) * 3600 + Number(temp[1]) * 60 + Number(temp[2])
        },
        handleResize() {
            this.screenHeight = document.body.clientHeight
            this.tableHeight = this.screenHeight - 10
        },
        changeHeight() {
            this.styObj.height = `${window.innerHeight}px`
        },
        downloadLog(row) {
            this.$Loading.start()
            const url = `http://localhost:8000/download/logs/?filepath=${row.downloadlurl}`
            window.location.href = url
            this.$Loading.finish()
        },
        fetchData() {
            getSpiderPageData().then((res) => {
                const msg = res.message
                this.urlstate = Number(msg.spiderstatelist[1][0]) === 1
                this.detailstate = Number(msg.spiderstatelist[2][0]) === 1
                this.urltime = msg.spiderstatelist[1][1]
                this.detailtime = msg.spiderstatelist[2][1]

                // 清空并重建图表数据
                this.xData = []
                this.yData = []
                Object.keys(msg.statistical).forEach((key) => {
                    this.xData.push(key)
                    this.yData.push(msg.statistical[key])
                })

                this.$nextTick(() => {
                    if (this.$refs.chart_line_one) {
                        this.$refs.chart_line_one.initChart(this.name, this.xData, this.yData)
                    }
                })

                const ignoreLogs = ['clg.log', 'hlg.log', 'rlg.log', 'log.log']

                this.UrlData = []
                Object.keys(msg.urlloglist).forEach((key) => {
                    if (ignoreLogs.includes(key)) return
                    this.UrlData.push({
                        name: key,
                        date: msg.urlloglist[key].time,
                        downloadlurl: msg.urlloglist[key].filepath,
                    })
                })

                this.DetailData = []
                Object.keys(msg.detaillist).forEach((key) => {
                    if (ignoreLogs.includes(key)) return
                    this.DetailData.push({
                        name: key,
                        date: msg.detaillist[key].time,
                        downloadlurl: msg.detaillist[key].filepath,
                    })
                })
            })
        },
        BeginDetailSpider() {
            if (this.detailstate) {
                const seconds = this.parseTimeToSeconds(this.detailtime)
                if (seconds === 0) {
                    this.$Message.error('请选择间隔时间')
                    this.detailstate = false
                } else {
                    detailspider(seconds, this.detailtime).then(() => {
                        this.$Message.info('详情爬虫状态：打开')
                        this.fetchData()
                    })
                }
            } else {
                closedetailspider().then((res) => {
                    if (res.message === '已关闭') {
                        this.$Message.info('详情爬虫状态：关闭')
                        this.fetchData()
                    }
                })
            }
        },
        BeginUrlSpider() {
            if (this.urlstate) {
                const seconds = this.parseTimeToSeconds(this.urltime)
                if (seconds === 0) {
                    this.$Message.error('请选择间隔时间')
                    this.urlstate = false
                } else {
                    urlspider(seconds, this.urltime).then(() => {
                        this.$Message.info('Url爬虫状态：打开')
                        this.fetchData()
                    })
                }
            } else {
                closeurlspider().then((res) => {
                    if (res.message === '已关闭') {
                        this.$Message.info('Url爬虫状态：关闭')
                        this.fetchData()
                    }
                })
            }
        },
    },
    created() {
        window.addEventListener('resize', this.changeHeight)
        this.changeHeight()
        this.fetchData()
    },
}
</script>

<style scoped>

</style>
