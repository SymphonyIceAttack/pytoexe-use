import numpy as np

class Matrixes():
    def __init__(self,filepath = 'record_1779605347.494491.txt'):
        '''
        直接从文件中寻找数据并构建矩阵
        :param filepath 文件路径
        '''
        self.filepath = filepath
        matrix = np.genfromtxt(filepath, delimiter=None, skip_header=1).astype(int)
        self.matrix = matrix[:, 1:].astype(int)

    def winlose_count(self):  
        '''
        统计最大值与最小值出现的次数，enumer自动为数据编号
        '''
        max_count = [0]*5
        min_count = [0]*5
        for row in self.matrix:
            maximum = max(row)
            minimum = min(row)
            for j,val in enumerate(row):
                if val == maximum:
                    max_count[j] += 1
                if val == minimum:
                    min_count[j] += 1
        return f'冠：{max_count}\n寄：{min_count}'
    
    def total_sum(self):
        for col_idx in range(self.matrix.shape[1]):
            col = self.matrix[:, col_idx]
            maximum = max(col)
            minimum = min(col)
            q10 = np.percentile(col, 10)
            q25 = np.percentile(col, 25)
            qmid = np.percentile(col, 50)
            q75 = np.percentile(col, 75)
            q90 = np.percentile(col, 90)
            yield f'中位数时长 (体现常规水平):{round(qmid/6000,4)}分钟\n下十分位 (10%):{round(q10/6000,4)}分钟\n下四分位 (25%):{round(q25/6000,4)}分钟\n上四分位 (75%):{round(q75/6000,4)}分钟\n上十分位 (90%):{round(q90/6000,4)}分钟\n最佳表现:{round(maximum/6000,4)}分钟\n最差表现:{round(minimum/6000,4)}分钟'
    def name_set(self):
        '''
        重新选定测试文件，delimiter为分隔符设置（None默认空），skip_header为跳过前n行，从第n+1行开始读取
        '''
        name = input('请输入需要查看冠寄的测试txt（record开头的那个）')
        self.filepath = name
        self.matrix = np.genfromtxt(name, delimiter=None, skip_header=1)[:,1:].astype(int)

document = Matrixes()
def data_handle():
    group = input('请输入参赛各队伍的编号（如270、1951）（用空格间隔）').split()
    for k,ch in enumerate(document.total_sum()):
        print(f'{group[k]}\n{ch}')

def run():
    document.name_set()
    print(document.winlose_count())
    data_handle()
    input()

if __name__ == '__main__':
    run()