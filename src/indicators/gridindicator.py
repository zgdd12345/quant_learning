import backtrader as bt

class GridIndicator(bt.Indicator):
    # 定义指标线名称（必须）
    # lines = ('custom_line',)  # 元组形式，可定义多个输出线
    
    # 参数设置（可选）
    params = (
        ('period', 30),      # 默认参数
        # ('datafield', 'close'),  # 可指定计算用的数据字段
        ('max_layers', 5), # 最大网格数量
        ('grid_space', 10) # 网格间距
    )

    lines = ('grid1', 'grid2', 'grid3', 'grid4', 'grid5')
    
    # 初始化计算方法（适用于向量化计算）
    def __init__(self):
        # 计算逻辑（示例：计算收盘价的移动平均）
        sma = bt.indicators.SMA(self.data.close, period=self.p.period)

        self.lines.grid1 = sma + self.p.grid_space * 2
        self.lines.grid2 = sma + self.p.grid_space * 1
        self.lines.grid3 = sma + self.p.grid_space * 0
        self.lines.grid4 = sma - self.p.grid_space * 1
        self.lines.grid5 = sma - self.p.grid_space * 2
    
    # 逐根K线计算方法（可选，与__init__二选一）
    # def next(self):
    #     # 示例：手动计算过去period天的收盘价平均值
    #     sum_close = sum(self.data.close[-i] for i in range(self.p.period))
    #     self.lines.custom_line[0] = sum_close / self.p.period
