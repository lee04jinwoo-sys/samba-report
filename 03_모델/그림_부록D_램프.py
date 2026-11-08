import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import sys
fm.fontManager.addfont('/System/Library/Fonts/AppleSDGothicNeo.ttc')
plt.rcParams.update({'font.family':'Apple SD Gothic Neo','axes.unicode_minus':False,'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
OUT=sys.argv[1]; B='#2a78d6'; O='#eb6834'; G='#898781'
# 값은 기존 그림(부록D_공장_램프.png) 생성 데이터 그대로. x축만 t=-4~8로 통일
t4=list(range(-4,13)); v4=[34.2,35.1,33.7,36.9,39.7,40.8,41.8,41.2,41.0,39.9,40.0,39.7,37.8,39.7,41.3,43.9,45.4]
t5=list(range(-4,6)); v5=[40.0,39.7,37.8,39.7,41.3,43.9,45.4,46.1,45.7,43.6]
t3=list(range(-4,9)); v3=[14.2,14.9,19.0,18.1,10.4,4.2,-3.5,-0.7,13.1,22.7,27.1,27.9,25.1]
cut=lambda t,v:[(a,b) for a,b in zip(t,v) if a<=8]
t4,v4=zip(*cut(t4,v4))
fig,ax=plt.subplots(figsize=(7,3.3),dpi=200)
ax.plot(t3,v3,color=G,marker='^',ms=4,lw=1.3,label='3공장 (t=0: 4Q18)')
ax.plot(t4,v4,color=B,marker='o',ms=4,lw=1.3,label='4공장 (t=0: 4Q22)')
ax.plot(t5,v5,color=O,marker='s',ms=4,lw=1.3,label='5공장 (t=0: 2Q25)')
ax.annotate('3Q26 (현재)',(t5[-1],v5[-1]),textcoords='offset points',xytext=(0,7),fontsize=8,color=O,va='bottom',ha='center')
ax.axvline(0,color='#c3c2b7',lw=1,ls='--'); ax.axhline(0,color='#c3c2b7',lw=0.8)
ax.set_xlim(-4.5,8.5); ax.set_xticks(range(-4,9,2))
ax.set_xlabel('가동 후 분기 (t)'); ax.set_ylabel('최근 4분기 합산 영업이익률 (%)'); ax.grid(axis='y',color='#e1e0d9',lw=0.8); ax.legend(frameon=False,fontsize=9,loc='lower right')
fig.tight_layout(); fig.savefig(f'{OUT}/부록D_공장_램프.png'); plt.close(fig); print('ok')
