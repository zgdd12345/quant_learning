import backtrader as bt
from indicator.gridindicator import GridIndicator


class GridTradingStrategyBase(bt.Strategy):
    params = (
        ('start_price', None),    # 初始基准价，None则用第一个K线收盘价
        ('grid_space', 100),       # 网格间距
        ('volume_per_layer', 100),# 每层交易量
        ('max_layers', 5),        # 最大交易层数
        ('print_log', True),       # 是否打印交易日志
        ('period', 20),
        ('subplot', False)
    )

    def __init__(self):

        # self.sma5 = bt.indicators.SimpleMovingAverage(self.data.close, period=5)
        self.sma30 = bt.indicators.SimpleMovingAverage(self.data.close, period=30, plot=False)
        self.grid_layers = GridIndicator(period=self.p.period, max_layers=self.p.max_layers, grid_space=self.p.grid_space, subplot=self.p.subplot)

        # 延迟到第一个K线初始化关键参数
        self.start_price = None
        self.buy_levels = []       # 买入价格网格
        self.active_buys = set()   # 当前持有的买入层级
        self.order = None          # 当前订单对象

    def next(self):
        # 延迟初始化（确保第一个K线数据到位）
        if self.start_price is None:
            self._initialize_grid()
            return
        self.buy_levels = [self.grid_layers.grid1[0], self.grid_layers.grid2[0], self.grid_layers.grid3[0], self.grid_layers.grid4[0], self.grid_layers.grid5[0]]
        # print(f'初始基准价: {self.start_price:.2f}')
        # print(f'买入网格: {[round(x,2) for x in self.buy_levels]}')
        # print(grid_levels[0])
        # self.buy_levels = [ float(level) for level in grid_levels]
        # self.buy_levels = [self.grid_layers.grid1, self.grid_layers.grid2, self.grid_layers.grid3, self.grid_layers.grid4, self.grid_layers.grid5]
        # print(f'重新计算买入网格: {[x for x in self.buy_levels]}')
        # 获取当前K线最低价和最高价
        current_low = self.data.low[0]
        current_high = self.data.high[0]

        # 执行网格买入逻辑
        self._execute_buys(current_low)
        
        # 执行网格卖出逻辑
        self._execute_sells(current_high)
        # if self.order:
        #     print(f'买入网格: {[round(x,2) for x in self.buy_levels]}')
        # self._reset_grid()


    def _initialize_grid(self):
        '''初始化网格参数'''
        if self.p.start_price is None:
            self.start_price = self.data.close[0]
        else:
            self.start_price = self.p.start_price
        
        # 生成买入价格网格（基准价下方）
        self.buy_levels = [self.start_price - i * self.p.grid_space for i in range(1, self.p.max_layers + 1)]
        if self.p.print_log:
            print(f'初始基准价: {self.start_price:.2f}')
            print(f'买入网格: {[round(x,2) for x in self.buy_levels]}')

    def _execute_buys(self, current_low):
        '''处理买入信号'''
        for level in self.buy_levels:
            # 满足条件：触及网格线+未持有+未达最大层数
            if (current_low <= level and (level not in self.active_buys) and len(self.active_buys) < self.p.max_layers):
                self.order = self.buy(size=self.p.volume_per_layer)
                self.active_buys.add(level)
                if self.p.print_log:
                    self.log(f'BUY EXECUTED, Price: {level:.2f}, Layers: {len(self.active_buys)}')

    def _execute_sells(self, current_high):
        '''处理卖出信号'''
        to_remove = []
        for level in self.active_buys:
            # 计算对应卖出价（买入价+网格间距）
            sell_price = level + self.p.grid_space
            
            # 满足条件：触及卖出价
            if current_high >= sell_price:
                self.order = self.sell(size=self.p.volume_per_layer)
                to_remove.append(level)
                if self.p.print_log:
                    self.log(f'SELL EXECUTED, Sell Price: {sell_price:.2f}, Buy Price: {level:.2f}')

        # 移除已卖出的层级
        for level in to_remove:
            self.active_buys.remove(level)

    def _reset_grid(self):
        dynamic_sma = self.sma30[0] + self.p.grid_space * 2
        self.buy_levels = [dynamic_sma - i * self.p.grid_space for i in range(1, self.p.max_layers + 1)]
        print(f'更新后的初始基准价: {dynamic_sma:.2f}', f'买入网格: {[round(x,2) for x in self.buy_levels]}')

    def notify_order(self, order):
        '''订单状态通知'''
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入成交，价格：{order.executed.price:.2f}, 数量：{order.executed.size}')
            elif order.issell():
                self.log(f'卖出成交，价格：{order.executed.price:.2f}, 数量：{order.executed.size}')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单异常：%s' % order.getstatusname())

    def log(self, txt, dt=None):
        '''日志记录'''
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    
    # 添加数据
    data = bt.feeds.YahooFinanceData(
        dataname='AAPL',
        fromdate=bt.datetime.parse('2020-01-01'),
        todate=bt.datetime.parse('2021-12-31')
    )
    cerebro.adddata(data)
    
    # 添加策略
    cerebro.addstrategy(GridTradingStrategyBase,
                       grid_space=5,
                       volume_per_layer=100,
                       max_layers=5)
    
    # 设置初始资金
    cerebro.broker.setcash(100000.0)
    
    # 运行回测
    print('初始资金: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    print('最终资金: %.2f' % cerebro.broker.getvalue())
