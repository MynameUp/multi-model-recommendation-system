<template>
    <div style="background:#eee;width: 100%; height: 100%; overflow: scroll;" >
        <Row>
            <Col span="8"  >
                <div style="background:#eee; padding: 20px;" :style="styObj" >
                    <Card :bordered="false">
                        <h3 slot="title">数据分析配置</h3>
                        <span>
                                <span style="margin-left: 5px; font-size: larger;">定时</span>
                                <span style="float: right;">
                                    <TimePicker v-model="analysistime"
                                                :steps="[1, 3, 60]" placeholder="Time" style="width: 112px"></TimePicker>
                                </span><br/><br/><br/>
                                <span style="margin-left: 5px; font-size: larger;" >启动/关闭数据分析</span>
                                <span style="float: right;">
                                    <i-switch v-model="analysisstate" @click.native="BeginAnalysis" />
                                </span>
                            </span>
                    </Card>
                    <Card :bordered="false" style="margin-top: 10px;">
                        <h3 slot="title">推荐配置</h3>
                        <span>
                                <span style="margin-left: 5px; font-size: larger;">定时推荐</span>
                                <span style="float: right;">
                                    <TimePicker v-model="recommendtime"
                                                :steps="[1, 5, 60]" placeholder="Time" style="width: 112px"></TimePicker>
                                </span><br/><br/><br/>
                                <span style="margin-left: 5px; font-size: larger;" >启动/关闭推荐</span>
                                <span style="float: right;">
                                    <i-switch v-model="recommendstate" @click.native="BeginRecommend" />
                                </span>
                            </span>
                    </Card>
                    <Card :bordered="false" style="margin-top: 10px;">
                        <h3 slot="title">运行情况</h3>
                        <ChartLint ref="chart_line_one" style="display: inline-block;"></ChartLint>
                    </Card>
                </div>
            </Col>
            <Col span="16">
                <div style="background:#eee;padding: 20px;" :style="styObj" >
                    <Card :bordered="false" style=" height: auto">
                        <h3 slot="title">新闻推荐日志</h3>
                        <Table style="height: auto" height="200" :columns="RecommendColumns"
                               :data="RecommendData" @on-row-click="downloadLog"></Table>
                    </Card>
                    <Card :bordered="false" style="margin-top: 10px;  height: auto;">
                        <h3 slot="title">数据分析日志</h3>
                        <Table style="height: auto" height="200" :columns="AnalysisColumns"
                               :data="AnalysisData" @on-row-click="downloadLog"></Table>
                    </Card>
                </div>
            </Col>
        </Row>
    </div>
</template>

<script>
// 1. 先导入带别名 (@) 的模块，再导入相对路径模块 [解决 import/order 错误]
import { recommendOff, recommendOn, analysisOn, analysisOff, getRecommendPageData } from '@/api'
import ChartLint from '../components/RecommendChartLint.vue'

export default {
    name: 'RecommendSystem',
    components: { ChartLint },
    data() {
        return {
            analysistime: '',
            analysisstate: false,
            recommendtime: '',
            recommendstate: false,
            name: '推荐量',
            xData: [],
            yData: [],
            RecommendColumns: [
                { title: '日志名', key: 'name' },
                { title: '时间', key: 'date' },
            ],
            RecommendData: [],
            AnalysisColumns: [
                { title: '日志名', key: 'name' },
                { title: '时间', key: 'date' },
            ],
            AnalysisData: [],
            styObj: { height: '0px' },
            screenHeight: 0,
            tableHeight: 0,
        }
    },
    mounted() {
        // [优化] 使用解构赋值并直接应用，避免 unused-vars 警告
        const { name, xData, yData } = this
        this.$refs.chart_line_one.initChart(name, xData, yData)

        // 使用 addEventListener 替代直接赋值，更符合规范
        window.addEventListener('resize', this.handleResize)
    },
    beforeDestroy() {
        // 组件销毁前移除监听，防止内存泄漏
        window.removeEventListener('resize', this.handleResize)
        window.removeEventListener('resize', this.changeHeight)
    },
    methods: {
        // [新增] 提取公共的时间解析逻辑
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
            this.styObj.height = window.innerHeight + 'px'
        },
        downloadLog(row) {
            this.$Loading.start()
            // 建议使用模板字符串
            const url = `http://localhost:8000/download/logs/?filepath=${row.downloadlurl}`
            window.location.href = url
            this.$Loading.finish()
        },
        BeginRecommend() {
            if (this.recommendstate) {
                const seconds = this.parseTimeToSeconds(this.recommendtime)
                if (seconds === 0) {
                    this.$Message.error('请选择间隔时间')
                    this.recommendstate = false
                } else {
                    recommendOn(seconds, this.recommendtime)
                    this.$Message.info('推荐系统状态：打开')
                }
            } else {
                recommendOff().then(res => {
                    if (res.message === 'Success.') {
                        this.$Message.info('推荐系统状态：关闭')
                    }
                })
            }
        },
        BeginAnalysis() {
            if (this.analysisstate) {
                const seconds = this.parseTimeToSeconds(this.analysistime)
                if (seconds === 0) {
                    this.$Message.error('请选择间隔时间')
                    this.analysisstate = false
                } else {
                    analysisOn(seconds, this.analysistime)
                    this.$Message.info('分析系统状态：打开')
                }
            } else {
                analysisOff().then(res => {
                    if (res.message === 'Success.') {
                        this.$Message.info('分析系统状态：关闭')
                    }
                })
            }
        },
    },
    created() {
        window.addEventListener('resize', this.changeHeight)
        this.changeHeight()

        getRecommendPageData().then(res => {
            const msg = res.message

            // 状态同步
            this.recommendstate = Number(msg.spiderstatelist[3][0]) === 1
            this.analysisstate = Number(msg.spiderstatelist[4][0]) === 1
            this.recommendtime = msg.spiderstatelist[3][1]
            this.analysistime = msg.spiderstatelist[4][1]

            // 图表数据转换 (替换 176 行附近)
            Object.keys(msg.statistical).forEach(i => {
                this.xData.push(i)
                this.yData.push(msg.statistical[i])
            })
            this.$refs.chart_line_one.initChart(this.name, this.xData, this.yData)

            // 列表数据过滤与填充 (替换 184 行附近)
            const ignoreRec = ['clg.log', 'hlg.log', 'rlg.log', 'log.log']
            Object.keys(msg.reclist).forEach(i => {
                if (ignoreRec.includes(i)) return // 用 return 替代 continue
                this.RecommendData.push({
                    name: i,
                    date: msg.reclist[i].time,
                    downloadlurl: msg.reclist[i].filepath,
                })
            })

            const ignoreAnalysis = ['ccg.log', 'hvg.log', 'hwg.log', 'log.log', 'kwg.log']
            Object.keys(msg.analysisloglist).forEach(i => {
                if (ignoreAnalysis.includes(i)) return // 用 return 替代 continue
                this.AnalysisData.push({
                    name: i,
                    date: msg.analysisloglist[i].time,
                    downloadlurl: msg.analysisloglist[i].filepath,
                })
            })
        })
    },
}
</script>

<style scoped>

</style>
