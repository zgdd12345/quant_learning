import pandas as pd
import  backtrader as bt
from datetime import datetime

from ..indicators.myindicator import DerivativeIndicator


class MyStrategy(bt.Strategy):
    params = (('myparam', 27), 
              ('exitbars', 5),
              ('maperiod', 20)
              )
    lines = ('derivative1', 'derivative2')
    
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)  # 注意要和datetime类型适配，使用datetime(0)表示当前时间 
        print('%s, %s' % (dt.isoformat(sep=" "), txt)) # dt.isoformat(sep=" ")格式化输出，以空格为date和time的分隔符

    def __init__(self):
        # 为每一列，创建一个bar
        self.dataopen = self.datas[0].open      # 开盘价bar  self.datas[0]指向的是大脑通过cerebro.adddata函数加载的第一个数据
        self.datahigh = self.datas[0].high      # 最高价bar
        self.datalow = self.datas[0].low        # 最低价bar
        self.dataclose = self.datas[0].close    # 收盘价bar self.datas[0].close指向的是close （收盘价）line
        self.datavolume = self.datas[0].volume  # 成交量bar
        
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.sma = bt.indicators.MovingAverageSimple(self.datas[0], period=self.params.maperiod)
        # print(self.datas[0])
        self.derivative1 = DerivativeIndicator(self.datas[0])
        # self.derivative2 = DerivativeIndicator(self.derivative1)
        # 增加划线的指标
        # bt.indicators.ExponentialMovingAverage(self.datas[0], period=25) # 指数移动平均线
        # bt.indicators.WeightedMovingAverage(self.datas[0], period=25, subplot=True) # 权重移动平均线
        # bt.indicators.StochasticSlow(self.datas[0]) # 随机指标
        # bt.indicators.MACDHisto(self.datas[0]) # MACD指标
        # rsi = bt.indicators.RSI(self.datas[0]) # RSI指标
        # bt.indicators.SmoothedMovingAverage(rsi, period=10) # 平滑移动平均线
        # bt.indicators.ATR(self.datas[0], plot=False) # ATR指标

    def notify_order(self, order):
        """
        订单状态的改变会通过notify方法通知到strategy。
        通过覆盖 notify_order() 方法监听订单状态（如提交、成交、取消或拒绝），实时更新 self.order 的状态信息‌
        """

        if order.status in [order.Submitted, order.Accepted]: # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
 
        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %(order.executed.price, order.executed.value, order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' % (order.executed.price,  order.executed.value, order.executed.comm))
            self.bar_executed = len(self) # 最后一次执行交易时bar的位置
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None # Write down: no pending order
    
    def notify_trade(self, trade):#交易执行后，在这里处理
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %(trade.pnl, trade.pnlcomm)) #记录下盈利数据。 Gross：毛利；Net:净利

    def next(self): 
        """
        strategy 的next方法针对self.dataclose(也就是收盘价Line)的每一行,也就是Bar,进行处理。
        next方法是Strategy最重要的的方法,
        具体策略的实现都在这个函数中，后续还会详细介绍。
        """
        self.log('Close, {:.2f}'.format(self.dataclose[0]))
        self.log('Derivative, {}'.format(self.derivative1.lines.derivative_volume[0]))
        # print(self.derivative1.lines.derivative_close)
        if self.order:  # Check if an order is pending ... if yes, we cannot send a 2nd one
            return

        if not self.position: # Check if we are in the market
            if self.dataclose[0] > self.sma[0]: # 大于均线就买 BUY, BUY, BUY!!! (with all possible default parameters)
                if self.derivative1.lines.derivative_volume[0] < 0 and self.derivative1.lines.derivative_volume[-1] < 0:
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.order = self.buy() # Keep track of the created order to avoid a 2nd order
        else:
            if self.dataclose[0] < self.sma[0]: # 小于均线卖卖卖！
                if self.derivative1.lines.derivative_volume[0] > 0 and self.derivative1.lines.derivative_volume[-1] > 0:
                    self.log('SELL CREATE, %.2f' % self.dataclose[0])
                    self.order = self.sell()  # Keep track of the created order to avoid a 2nd order