<template>
    <div class="home-container">
        <div class="home-content" style="overflow: scroll; height: 100%;" >
            <div class="circle" style=" white-space: nowrap;">
                <ChartLint ref="chart_line_one" style="display: inline-block;"></ChartLint>
                <div class="content" style="display: inline-block;">
                    <i-circle
                        :percent="75"
                        :size="300"
                        :trail-width="4"
                        :stroke-width="5"
                        stroke-linecap="square"
                        stroke-color="#43a3fb" style="margin-left: 5px;">
                        <div class="demo-Circle-custom">
                            <h1>42,001,776</h1>
                            <p>消费人群规模</p>
                            <span>
                    总占人数
                    <i>75%</i>
                </span>
                        </div>
                    </i-circle>
                    <i-circle
                        :percent="percent"
                        :size="300"
                        :trail-width="4"
                        :stroke-width="5"
                        stroke-linecap="square"
                        :stroke-color="circleColor"
                        style="margin-left: 5px;">
                        <div class="demo-Circle-custom">
                            <h1>42,001,776</h1>
                            <p>消费人群规模</p>
                            <span>
                                总占人数 <i>{{ percent }}%</i>
                            </span>
                        </div>
                    </i-circle>
                </div>
            </div>
            <Divider/>
            <div class="chart" style="height: 60%;">
                <Table :height="tableHeight" border :columns="columns5" :data="data5"></Table>
            </div>
        </div>
        <footer>
            <div style="text-align: center; background: #656565">
                <span style="color: white">Copyright © 2021 News| 京ICP备xxxxxxx号-1 </span>
            </div>
        </footer>
    </div>
</template>

<script>
import ChartLint from '../components/MainPageChartLint'

export default {
    name: 'home',
    components: { ChartLint },
    data() {
        return {
            // [优化] 建议将个人信息改为更具项目相关性的名称，例如“系统运行概览”
            name: '系统活跃度',
            xData: ['2020-02', '2020-03', '2020-04', '2020-05'],
            yData: [30, 132, 80, 134],
            tableHeight: window.innerHeight - 510,
            screenHeight: document.body.clientHeight,
            columns5: [
                { title: 'Date', key: 'date', sortable: true },
                { title: 'Name', key: 'name' },
                { title: 'Age', key: 'age', sortable: true },
                { title: 'Address', key: 'address' },
            ],
            data5: [
                { name: 'John Brown', age: 18, address: 'New York No. 1 Lake Park', date: '2016-10-03' },
                { name: 'Jim Green', age: 24, address: 'London No. 1 Lake Park', date: '2016-10-01' },
                { name: 'Joe Black', age: 30, address: 'Sydney No. 1 Lake Park', date: '2016-10-02' },
                { name: 'Jon Snow', age: 26, address: 'Ottawa No. 2 Lake Park', date: '2016-10-04' },
                { name: 'Jon Snow', age: 26, address: 'Ottawa No. 2 Lake Park', date: '2016-10-04' },
                { name: 'Jon Snow', age: 26, address: 'Ottawa No. 2 Lake Park', date: '2016-10-04' },
                { name: 'Jon Snow', age: 26, address: 'Ottawa No. 2 Lake Park', date: '2016-10-04' },
                { name: 'Jon Snow', age: 26, address: 'Ottawa No. 2 Lake Park', date: '2016-10-04' },
            ],
            // [优化] 将 percent 初始值设为 75 以匹配 UI 显示
            percent: 75,
        }
    },
    computed: {
        circleColor() {
            let color = '#2db7f5'
            if (this.percent === 100) {
                color = '#5cb85c'
            }
            return color
        },
    },
    mounted() {
        // [修复] 消除 unused-vars 警告：直接将解构后的变量用于初始化
        const { name, xData, yData } = this
        this.$refs.chart_line_one.initChart(name, xData, yData)

        // [优化] 使用 addEventListener 代替 window.onresize 赋值，避免覆盖其他页面的逻辑
        window.addEventListener('resize', this.handleResize)
    },
    beforeDestroy() {
        // [关键] 组件销毁前必须移除监听器，防止内存泄漏或控制台报错
        window.removeEventListener('resize', this.handleResize)
    },
    methods: {
        handleResize() {
            this.screenHeight = document.body.clientHeight
            this.tableHeight = this.screenHeight - 510 // 保持高度比例一致
        },
        add() {
            if (this.percent >= 100) return
            this.percent += 10
        },
        minus() {
            if (this.percent <= 0) return
            this.percent -= 10
        },
    },
}
</script>

<style scoped>
.home-container {
    padding: 10px;
    padding-top: 5px;
}

.home-content {
    padding: 10px;
    border-radius: 5px;
    background: #fff;
}
</style>
<style lang="less">
.demo-Circle-custom {
    & h1 {
        color: #3f414d;
        font-size: 28px;
        font-weight: normal;
    }

    & p {
        color: #657180;
        font-size: 14px;
        margin: 10px 0 15px;
    }

    & span {
        display: block;
        padding-top: 15px;
        color: #657180;
        font-size: 14px;

        &:before {
            content: '';
            display: block;
            width: 50px;
            height: 1px;
            margin: 0 auto;
            background: #e0e3e6;
            position: relative;
            top: -15px;
        }
    ;
    }

    & span i {
        font-style: normal;
        color: #3f414d;
    }
}
</style>
