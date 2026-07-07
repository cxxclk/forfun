# -*- coding: utf-8 -*-
import base64, io, json
from PIL import Image

BASE = '/sessions/lucid-practical-feynman/mnt/outputs'
MAPD = '/sessions/lucid-practical-feynman/mnt/Path Optimization'
OUT = f'{MAPD}/策略分析.html'

def b64(path, width=900, q=78):
    im = Image.open(path)
    if im.width > width:
        im = im.resize((width, int(im.height*width/im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.convert('RGB').save(buf, 'JPEG', quality=q)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()

R = json.load(open(f'{BASE}/plan_result.json'))
D = json.load(open(f'{MAPD}/Map/map_data.json'))
Z = D['zones']
plans = R['plans']
RANKMARK = lambda n: '☆' if (Z[n].get('difficulty') or 5) <= 2 else ('▲' if (Z[n].get('difficulty') or 5) == 7 else '')

def caplist(side, wk):
    zs = plans[side][str(wk)].get('new_captures', [])
    return '、'.join(f"{n}({Z[n]['monster']}){RANKMARK(n)}" for n in zs)

def annot(zs):
    return '、'.join(f"{n}{RANKMARK(n)}" for n in zs)

def holdline(side, wk):
    zs = plans[side][str(wk)]['hold']
    return annot(sorted(zs, key=lambda n: (-Z[n]['level'], n)))

OURPLAN = {
 1: ['2-1','2-2','2-17','2-10','2-5','2-15','2-4','2-13','2-18','1-15'],
 2: ['3-6','3-13','3-5','3-12','3-1','3-4','3-11','3-8','2-16','2-1'],
 3: ['4-12','4-7','4-2','4-1','4-6','4-11','4-14','4-4','3-6','3-13'],
 4: ['5-8','5-9','5-3','5-2','5-7','5-10','5-5','4-7','4-6','4-4'],
 5: ['6-1','6-2','6-3','6-4','5-8','5-9','5-3','5-2','5-7','5-10'],
 6: ['7-1','7-2','7-3','6-1','6-2','6-3','6-4','5-8','5-9','5-3'],
}
def ourhold(wk):
    zs = OURPLAN[wk]
    s = sum({1:150,2:300,3:600,4:1200,5:2400,6:7200,7:21600}[Z[n]['level']] for n in zs)
    return annot(zs), s

weekimgs = ''.join(
    f'<img src="{b64(f"{BASE}/r_week{w}.png", 820, 72)}" alt="week{w}">' for w in range(1,7))
caprows = ''.join(
    f"<tr><td>{wk}</td><td>{caplist('W', wk)}</td><td>{caplist('E', wk)}</td></tr>" for wk in range(1,7))

html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>攻城策略分析</title><style>
body{{font-family:system-ui,'Microsoft YaHei',sans-serif;max-width:960px;margin:0 auto;padding:24px;background:#1e2119;color:#e8e6d9;line-height:1.75}}
h1{{font-size:24px;border-bottom:2px solid #5a7d4a;padding-bottom:8px}}
h2{{font-size:19px;color:#a8c686;margin-top:32px}}
img{{max-width:100%;border-radius:8px;margin:10px 0;display:block}}
table{{border-collapse:collapse;width:100%;font-size:13.5px;margin:12px 0}}
td,th{{border:1px solid #4a5140;padding:6px 9px;text-align:left;vertical-align:top}}
th{{background:#2d3226}}
.key{{background:#2d3226;border-left:4px solid #d4a017;padding:10px 14px;border-radius:0 8px 8px 0;margin:14px 0}}
.rec{{background:#26301f;border-left:4px solid #7ec850;padding:10px 14px;border-radius:0 8px 8px 0;margin:14px 0}}
.warn{{color:#d4a017}}
details{{margin:10px 0}} summary{{cursor:pointer;color:#a8c686}}
.sm{{font-size:12.5px;color:#b9c4a5}}
</style></head><body>
<h1>攻城策略分析 v5（邻接已校对 · 含我方路线推荐）</h1>
<div class="rec">🛠 <a href="planner.html" style="color:#7ec850;font-weight:bold">互动战况计算器</a>：在地图上标记敌我持有，实时计算日结算分、推荐进攻、锁死进度、防守前线与寻路。文末有内嵌版。</div>
<p>规则见 <b>rules.yaml</b>。开放顺序按<b>地图颜色</b>（约每周一档）：第1周=1级+9座贴边2级(2-1/2-2/2-4/2-5/2-10/2-13/2-15/2-17/2-18)，第2周=其余2级+全部3级，第3周=4级，以此类推，第6周=7级，<b>8-1最后单独开放</b>。贴地图边缘的31座城开放后随时可进，其余需相邻跳板。怪物难度（个人积分，越易越好刷）：暴食1 &lt; 巨魔2 &lt; 看守者3 &lt; 风暴4 &lt; 章鱼/烈焰/钻头/元素=7。<span class="warn">未计入：首占奖励数值、个人积分公式、8-1（混沌）分数。</span></p>

<h2>一、分数结构：后期压倒一切</h2>
<div class="key">一座7级城<b>一天</b> = 21600 ≈ 前期一整周总收益。前两周分数无关紧要，值钱的是首占奖励、卡位、用易怪刷个人积分。5级11座、6级4座、7级3座——从第4周起必然不够分。</div>

<h2>二、全图咽喉（按校对后邻接更新）</h2>
<img src="{b64(f'{BASE}/r_battleground.png')}">
<table>
<tr><th>目标</th><th>入口</th><th>说明</th></tr>
<tr><td>7-1（风暴4）</td><td>6-2、6-4 ＋ 7-2/7-3</td><td>最好打的7级</td></tr>
<tr><td>7-2（钻头7）</td><td>5-9、6-3 ＋ 7-1/7-3</td><td>5-9 是唯一5级入口</td></tr>
<tr><td>7-3（烈焰7）</td><td>5-8、6-1、6-4 ＋ 7-1/7-2</td><td>入口最多</td></tr>
<tr><td>8-1（混沌）</td><td><b>仅 7-1、7-2、7-3</b></td><td>没有低级旁路</td></tr>
</table>
<div class="key">校对后两个结构性变化：① <b>8-1 只能从7级城进入</b>（6-3 旁路不存在了）→ 独占三座7级 = 完全垄断8-1。② <b>三座7级互相连通</b> → 拿下任意一座，就获得对另外两座的进攻权：突破一点即可横扫7级环。5-8（暴食,易）/5-9（章鱼,难）仍是仅有的两个5级直通口，第4周的核心卡位点。</div>

<h2>三、怪物难度地理：东易西难</h2>
<p>最难档（章鱼/烈焰/钻头/元素）西 20 只 vs 东 10 只；最易的暴食东 9 vs 西 5。整季推进西方要啃 14 座难档城、东方 12 座。<b>东半区城池分与个人积分双优。</b></p>

<h2>四、方案一：协商分治</h2>
<img src="{b64(f'{BASE}/r_partition.png')}">
<p>东西分治：西拿 6-1、6-3、7-2，东拿 6-2、6-4、7-1，<b>7-3 与 8-1 决战</b>。7-3 入口：西持 5-8/6-1，东持 6-4——西 2:1 占地利，对冲东半区怪好打的优势。注意 7级互通后，<b>决战期各自的7级城就是对方的跳板</b>：拿下 7-3 的一方可顺势威胁另一方的 7-1/7-2，协议里要约定7级城互不侵犯、只争 7-3/8-1。</p>
<table>
<tr><th>周</th><th>动作要点</th><th>每日分（西/东）</th></tr>
<tr><td>1</td><td>只开1级+9座贴边2级：全占己方贴边2级（西3座/东6座）+1级凑满10；先打暴食/巨魔<br><span class="sm">西持：{holdline('W',1)}<br>东持：{holdline('E',1)}</span></td><td>1950 / 2400</td></tr>
<tr><td>2</td><td>其余2级+全部3级开放：换持全部3级+2级补位；<b>3-1(西)/3-4(东)贴边可直入</b><br><span class="sm">西持：{holdline('W',2)}<br>东持：{holdline('E',2)}</span></td><td>5100 / 5100</td></tr>
<tr><td>3</td><td>换持全部4级+3座3级<br><span class="sm">西持：{holdline('W',3)}<br>东持：{holdline('E',3)}</span></td><td>10200 / 10200</td></tr>
<tr><td>4</td><td>5级各5座；<b>西周五必拿 5-8（暴食,易）</b>，东拿 5-9<br><span class="sm">西持：{holdline('W',4)}<br>东持：{holdline('E',4)}</span></td><td>18000 / 18000</td></tr>
<tr><td>5</td><td>各占2座6级；东经 6-4 补占 5-8?——按协议 5-8 归西<br><span class="sm">西持：{holdline('W',5)}<br>东持：{holdline('E',5)}</span></td><td>30000 / 31200</td></tr>
<tr><td>6</td><td>各取己方7级 → 决战 7-3 + 8-1<br><span class="sm">西持：{holdline('W',6)}<br>东持：{holdline('E',6)}</span></td><td>50400+ / 51600+</td></tr>
</table>
<p class="sm">累计（每周3结算日）：西约34.7万、东约35.5万，7-3赢家末周再+约6.1万。注意第1周东方贴边2级6座vs西方3座——东半区第三项优势，谈判筹码again。</p>
<details><summary>每周新占清单（☆易怪 ▲难档）</summary>
<table><tr><th>周</th><th>西</th><th>东</th></tr>{caprows}</table></details>
<details><summary>各周持有集地图</summary>{weekimgs}</details>

<h2>五、方案二：全力对战</h2>
<img src="{b64(f'{BASE}/r_lockdown.png')}">
<div class="key">杀招不变且更硬：<b>9城锁死</b> = {{6-1、6-2、6-3、6-4、5-8、5-9}} + {{7-1、7-2、7-3}} ≤ 10城。8-1 现在没有 6-3 旁路，锁死后对手连理论翻盘点都没有。反过来也要警惕：<b>只要漏一座7级给对手，他就能沿 7级环反推</b>——锁死要么做全，要么在6级环就掐死对手。</div>

<h2>六、我方路线推荐（实力占优方）★</h2>
<div class="rec"><b>结论：不必急于选边站。走"以战促和"——按全力对战的路线推进卡位，第4周末视对方姿态再定打或谈。</b>理由：我方实力占优，卡位成功后既能全取（锁死），也能以既成事实换一份优厚协议（东半区+7-3 或 5-8/5-9 双门户），进可攻退可谈；而这套卡位动作在两种结局下都不浪费。</div>
<img src="{b64(f'{BASE}/r_route.png')}">
<p><b>双走廊推进</b>（避开难怪，全程以暴食/巨魔/看守者为主）：</p>
<table>
<tr><th>周</th><th>动作</th><th>目的</th></tr>
<tr><td>1</td><td>只开1级+贴边2级：首占 <b>2-1(看守者,贴边)</b> 与尽量多的贴边2级（2-17/2-2/2-10 易怪优先），北路站上 1-15</td><td>贴边2级是第1周唯一的300分城，抢首占<br><span class="sm">周末持有({ourhold(1)[1]}/日)：{ourhold(1)[0]}</span></td></tr>
<tr><td>2</td><td>2/3级全开：北路 1-15→2-8(看守者)→<b>2-16(巨魔)</b>；其余名额持易怪3级刷分（3-6/3-13/3-5/3-12…）</td><td>北路跳板就位+刷分侦察<br><span class="sm">周末持有({ourhold(2)[1]}/日)：{ourhold(2)[0]}</span></td></tr>
<tr><td>3</td><td>北路 2-16→<b>4-12(暴食)</b>；南路 2-1→<b>4-7(暴食)</b>；其余持易怪4级</td><td>站上两个6级环跳板，均为暴食<br><span class="sm">周末持有({ourhold(3)[1]}/日)：{ourhold(3)[0]}</span></td></tr>
<tr><td>4</td><td><b>决胜卡位</b>：周五开门 4-12→<b>5-8(暴食)</b>。5-9(章鱼)入口在 4-4/4-6，若对方染指也要抢（我方更强打得起消耗）。其余名额补易怪5级（5-3/5-2/5-7/5-10）</td><td>5-8 = 6-1/6-4/7-3 三重门户；握住它 7级环半开<br><span class="sm">周末持有({ourhold(4)[1]}/日)：{ourhold(4)[0]}（5-9没抢到则换4-12）</span></td></tr>
<tr><td>5</td><td><b>决胜争夺</b>：周五 5-8→6-1(巨魔)、6-4(看守者)；南路 4-7→6-2(暴食)；再 6-1→6-3(章鱼) 或 6-2→5-9 补刀。目标4座6级全拿，至少3座+不让对方碰 5-8/5-9</td><td>6级环全握 = 下周锁死已定局<br><span class="sm">周末持有({ourhold(5)[1]}/日)：{ourhold(5)[0]}</span></td></tr>
<tr><td>6</td><td>周五 5-8/6-1→<b>7-3</b>，随即 7-3→<b>7-2</b>（利用7级互通省去打 5-9/6-3 跳板），6-2/6-4→<b>7-1</b>。弃3座5级腾名额，终局持有=9城锁死+1机动。8-1 开放即从任意7级进攻</td><td>3×21600/天 + 独占8-1<br><span class="sm">周末持有({ourhold(6)[1]}/日)：{ourhold(6)[0]}</span></td></tr>
</table>
<p class="sm">注：持有清单指周日结算时的10城；周内可临时占中转城再放弃（如 2-8→2-16 链）。☆=易怪，▲=难档。</p>
<p><b>要点：</b>① 攻坚永远按怪物难度排序：6-2(暴食)→6-1(巨魔)→6-4(看守者)→6-3(章鱼)，7-1(风暴4)是最软的7级，若周五时间紧先拿它保结算分。② 每周日结算前兵力收缩防守：W4守5-8，W5守6级环，W6守三座7级——对手掉分靠抢我们结算前的城，锁死组合连片易守。③ 若第4周末对方明确避战（没来抢5-8/5-9/6级邻位），可转谈判：我们已握全部门户，条件随便开——比如我们拿东半区+7-3，让出西半区让他安心刷分。</p>

<h2>七、互动战况计算器</h2>
<p>标记敌我持有城，实时算分/推荐/寻路。<a href="planner.html" style="color:#7ec850">全屏打开 ↗</a></p>
<iframe src="planner.html" loading="lazy" style="width:100%;height:720px;border:1px solid #4a5140;border-radius:8px;background:#1e2119"></iframe>

<h2>八、待补充</h2>
<p>① 首占奖励数值；② 个人积分公式；③ 8-1 分数与具体开放时间（已知为颜色序最后一档）。改 rules.yaml 后一键重跑（Map/scripts/）。</p>
</body></html>"""

open(OUT, 'w', encoding='utf-8').write(html)
print('report KB:', len(html)//1024)
