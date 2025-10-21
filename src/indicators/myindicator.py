import backtrader as bt

# class DerivativeIndicator(bt.Indicator):
#     lines = ('derivative_close', 
#              'derivative_volume',
#              'derivative_open',
#              'derivative_high',
#              'derivative_low')  # 定义导数输出线‌:ml-citation{ref="1,2" data="citationList"}
    
#     def __init__(self):
#         self.addminperiod(2)  # 确保至少2个数据点才启动计算‌:ml-citation{ref="3,5" data="citationList"}
    
#     def next(self):
#         # if len(self.data) >= 2:  # 防止索引越界‌:ml-citation{ref="4,5" data="citationList"}
#         #     # print(self.lines.derivative_close)
#         #     # self.lines.derivative_close[0] = self.data.close[0] - self.data.close[-1]  # 存储计算结果‌:ml-citation{ref="1,5" data="citationList"}
#         #     # print(self.data.volume - self.data.volume[-1])
#         #     self.lines.derivative_volume[0] = self.data.volume[0] - self.data.volume[-1]
#         #     print(len(self.lines.derivative_volume), self.data.volume[0], self.data.volume[-1],self.lines.derivative_volume[0], )
#         #     # self.lines.derivative_open[0] = self.data.open[0] - self.data.open[-1]
#         #     # self.lines.derivative_high[0] = self.data.high[0] - self.data.high[-1]
#         #     # self.lines.derivative_low[0] = self.data.low[0] - self.data.low[-1]
#         try:
#             self.lines.derivative_volume[0] = self.data.volume[0] - self.data.volume[-1]
#             print(len(self.lines.derivative_volume), self.data.volume[0], self.data.volume[-1], self.lines.derivative_volume[0])
#         except IndexError:
#             print("Index out of range. Skipping calculation.")


class DerivativeIndicator(bt.Indicator):
    # 定义导数输出线
    lines = ('derivative_close', 
             'derivative_volume',
             'derivative_open',
             'derivative_high',
             'derivative_low')
    
    def __init__(self):
        # 确保至少有 2 个数据点才开始计算
        self.addminperiod(2)
    
    def next(self):
        # 计算收盘价的导数
        # self.lines.derivative_close[0] = self.data.close[0] - self.data.close[-1]
        
        # 计算成交量的导数
        self.lines.derivative_volume[0] = self.data.volume[0] - self.data.volume[-1]
        
        # # 计算开盘价的导数
        # self.lines.derivative_open[0] = self.data.open[0] - self.data.open[-1]
        
        # # 计算最高价的导数
        # self.lines.derivative_high[0] = self.data.high[0] - self.data.high[-1]
        
        # # 计算最低价的导数
        # self.lines.derivative_low[0] = self.data.low[0] - self.data.low[-1]
        
        # 打印调试信息（可选）
        # print(f"Close Derivative: {self.lines.derivative_close[0]}, "
        #       f"Volume Derivative: {self.lines.derivative_volume[0]}")
