from pathlib import Path
import sys, json
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.cookie_cat import load_and_validate, analyze, stress_test, build_decision_memo, save_outputs

st.set_page_config(page_title="Cookie Cat | Experiment Decision Lab", page_icon="🧪", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink:#eef5ee; --muted:#9aa99f; --paper:#0c100e; --panel:#151c18; --lime:#d7ff62; --green:#8df0a9; --orange:#ffad66; --line:#29362e; }
html, body, [class*="css"] { font-family:'Manrope',sans-serif; }
.stApp { background:radial-gradient(ellipse at 82% 0%,rgba(91,128,69,.16),transparent 30%),radial-gradient(ellipse at 0% 50%,rgba(97,60,128,.10),transparent 36%),var(--paper); color:var(--ink); }
.block-container { padding-top:1.2rem; max-width:1480px; padding-bottom:3rem; }
[data-testid="stSidebar"] { background:#080b09; border-right:1px solid #202a23; }
[data-testid="stSidebar"] * { color:#edf5ed !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding:.48rem .7rem; border-radius:10px; transition:background .2s, transform .2s; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:#1a261e; transform:translateX(3px); }
.hero { background:linear-gradient(115deg,#18251c 0%,#111916 54%,#211b27 100%); color:#f5f7ef; padding:2.4rem 2.5rem; border:1px solid #354638; border-radius:26px; position:relative; overflow:hidden; box-shadow:0 22px 70px rgba(0,0,0,.24); animation:rise .65s ease both; }
.hero:before { content:''; position:absolute; inset:0; pointer-events:none; opacity:.18; background-image:linear-gradient(rgba(215,255,98,.10) 1px,transparent 1px),linear-gradient(90deg,rgba(215,255,98,.10) 1px,transparent 1px); background-size:32px 32px; mask-image:linear-gradient(90deg,black,transparent 82%); }
.hero:after { content:''; position:absolute; width:310px; height:310px; right:-85px; top:-150px; border:1px solid rgba(215,255,98,.25); border-radius:50%; box-shadow:0 0 0 26px rgba(215,255,98,.025),0 0 0 58px rgba(215,255,98,.025),0 0 85px rgba(215,255,98,.08); animation:orbit 16s linear infinite; }
.hero-kicker { color:var(--lime); font-family:'DM Mono',monospace; font-size:.72rem; letter-spacing:.16em; text-transform:uppercase; position:relative; }
.hero h1 { font-size:clamp(2.3rem,4.5vw,4.4rem); letter-spacing:-.075em; line-height:.98; margin:.9rem 0 1rem; color:#f5f7ef; font-weight:800; position:relative; }
.hero p { color:#bdcbbf; max-width:680px; font-size:1rem; line-height:1.7; position:relative; }
.hero-chip { display:inline-block; border:1px solid #526b55; background:rgba(12,16,14,.55); padding:.42rem .75rem; border-radius:99px; margin:.45rem .35rem 0 0; font-size:.72rem; color:#e0ebdf; position:relative; }
.kpi { background:linear-gradient(145deg,#1a241d,#121814); border:1px solid #2a3a2e; border-radius:18px; padding:1.1rem 1.15rem; min-height:122px; transition:transform .22s,border-color .22s,box-shadow .22s; animation:rise .55s ease both; }
.kpi:hover { transform:translateY(-5px); border-color:#9ec66a; box-shadow:0 12px 34px rgba(0,0,0,.22); }
.kpi-label { color:#9bab9e; font-family:'DM Mono',monospace; font-size:.68rem; text-transform:uppercase; letter-spacing:.1em; font-weight:500; }
.kpi-value { color:#f3f8f1; font-size:clamp(1.5rem,2.4vw,2.15rem); font-weight:800; letter-spacing:-.06em; margin:.48rem 0; }
.kpi-foot { color:#9bab9e; font-size:.76rem; }
.pulse-dot { display:inline-block; width:7px; height:7px; background:#a6ff72; border-radius:50%; margin-right:.45rem; box-shadow:0 0 0 0 rgba(166,255,114,.55); animation:pulse 1.8s infinite; }
.quest-track { display:flex; align-items:center; gap:0; margin:1.2rem 0 1.6rem; padding:1rem 1.1rem; background:linear-gradient(100deg,#131b16,#171a19); border:1px solid #29372e; border-radius:18px; overflow:hidden; }
.quest-node { flex:1; display:flex; align-items:center; gap:.65rem; min-width:0; }
.quest-orb { width:36px; height:36px; flex:0 0 36px; display:grid; place-items:center; border-radius:12px; border:1px solid #35443a; background:#202922; color:#9aa99f; font-family:'DM Mono',monospace; font-size:.8rem; }
.quest-node.done .quest-orb { background:#d7ff62; border-color:#d7ff62; color:#11170e; box-shadow:0 0 22px rgba(215,255,98,.15); }
.quest-node.active .quest-orb { border-color:#a7e86e; color:#d7ff62; box-shadow:0 0 0 4px rgba(215,255,98,.07); }
.quest-name { color:#dce7de; font-size:.75rem; font-weight:800; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.quest-state { color:#87988b; font-family:'DM Mono',monospace; font-size:.62rem; text-transform:uppercase; letter-spacing:.08em; }
.quest-link { height:1px; flex:0 0 24px; background:#334238; margin:0 .55rem; }
.section-kicker { color:var(--lime); font-family:'DM Mono',monospace; text-transform:uppercase; letter-spacing:.14em; font-size:.7rem; margin-bottom:.55rem; }
.panel { background:#151c18; border:1px solid #29362e; border-radius:20px; padding:1.1rem 1.2rem; }
.big-decision { padding:1.35rem 1.5rem; background:linear-gradient(120deg,#1b2a1f,#17221a); border:1px solid #3c5a40; border-radius:20px; box-shadow:inset 4px 0 0 var(--lime); }
.big-decision h3 { margin:.2rem 0; color:#d7ffb3; }
.big-decision p { color:#c3d0c5; }
.small-note { color:#9aa99f; font-size:.82rem; }
[data-testid="stMetric"] { background:linear-gradient(145deg,#1a241d,#121814); padding:1rem; border-radius:16px; border:1px solid #2a3a2e; }
[data-testid="stMetricLabel"] { color:#a8b8ac !important; }
[data-testid="stMetricValue"] { color:#f2f7f1 !important; }
.stButton>button, .stDownloadButton>button { border-radius:12px; font-weight:800; border:1px solid #60744c; background:linear-gradient(120deg,#d7ff62,#a7e86e); color:#10170f; transition:transform .18s,filter .18s,box-shadow .18s; }
.stButton>button:hover, .stDownloadButton>button:hover { color:#10170f; transform:translateY(-2px); filter:brightness(1.06); box-shadow:0 8px 24px rgba(215,255,98,.12); }
.stProgress > div > div { background:linear-gradient(90deg,#8df0a9,#d7ff62); }
[data-testid="stContainer"] { transition:border-color .2s; }
[data-testid="stAlert"] { border-radius:14px; }
hr { border-color:#29362e; }
[data-testid="stDataFrame"], [data-testid="stTable"] { border:1px solid #29362e; border-radius:12px; overflow:hidden; }
@keyframes rise { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
@keyframes orbit { to { transform:rotate(360deg); } }
@keyframes pulse { 0% { box-shadow:0 0 0 0 rgba(166,255,114,.5); } 70% { box-shadow:0 0 0 7px rgba(166,255,114,0); } 100% { box-shadow:0 0 0 0 rgba(166,255,114,0); } }
@media (max-width:720px) { .quest-track { align-items:flex-start; flex-direction:column; gap:.65rem; } .quest-link { width:1px; height:12px; flex:0 0 12px; margin:0 0 0 17px; } }
@media (prefers-reduced-motion:reduce) { *,*:before,*:after { animation:none !important; transition:none !important; } }
</style>
""", unsafe_allow_html=True)

def get_data():
    path = ROOT / "data" / "raw" / "cookie_cats.csv"
    if not path.exists():
        return None, None
    try:
        df = load_and_validate(path)
        return df, analyze(df)
    except Exception as e:
        return None, {"error": str(e)}

st.sidebar.markdown("## 🧪 Cookie Cat")
st.sidebar.caption("EXPERIMENT DECISION LAB")
page = st.sidebar.radio("Navigate", ["Quest Arcade", "Decision room", "Stress test", "Player signals", "Method & data", "Toolchain"], label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.markdown("**Your mission**")
st.sidebar.caption("Decide whether moving the level gate from 30 to 40 is worth shipping—without confusing statistical significance with product value.")
st.sidebar.divider()
# Session-scoped game progress: never changes or edits the source experiment data.
if "cc_xp" not in st.session_state:
    st.session_state.cc_xp = 0
if "cc_completed" not in st.session_state:
    st.session_state.cc_completed = []
st.sidebar.markdown("### 🏆 Investigator profile")
st.sidebar.markdown(f"**{st.session_state.cc_xp} XP** · Rank {1 + st.session_state.cc_xp // 100}")
st.sidebar.progress(min(1.0, (st.session_state.cc_xp % 100) / 100), text=f"{st.session_state.cc_xp % 100}/100 XP to next rank")
st.sidebar.caption(f"{len(st.session_state.cc_completed)}/4 missions cleared")
st.sidebar.caption("COOKIE CATS • PUBLIC EXPERIMENT DATA")
df, result = get_data()
if df is None:
    st.markdown('<div class="hero"><div class="hero-kicker">PRODUCT EXPERIMENTS / 001</div><h1>Don’t just find a winner.<br>Stress-test the decision.</h1><p>Cookie Cat turns the classic Cookie Cats experiment into an interactive decision lab. Start by loading the real public dataset; results are never invented or silently hardcoded.</p><span class="hero-chip">Evidence first</span><span class="hero-chip">Uncertainty visible</span><span class="hero-chip">Human decision</span></div>', unsafe_allow_html=True)
    st.warning("The validated dataset is not available yet." if not result or "error" not in result else f"Dataset validation failed: {result['error']}")
    st.markdown("### Start here")
    st.write("Use the project runner to automatically download and validate the public dataset:")
    st.code("python run_all.py", language="powershell")
    st.write("If the download succeeds, restart or refresh this app. The dashboard will then calculate all metrics from the data.")
    st.info("The original resume figures are project acceptance criteria, not placeholder values. They are only marked reproduced after the real data has been analyzed.")
    st.stop()

r7 = result["retention_7"]
g30 = next(g for g in result["groups"] if g["group"] == "gate_30")
g40 = next(g for g in result["groups"] if g["group"] == "gate_40")
st.markdown('<div class="hero"><div class="hero-kicker">PRODUCT EXPERIMENTS / 001 · COOKIE CATS</div><h1>Don’t just find a winner.<br>Stress-test the decision.</h1><p>One experiment. Two gate placements. A decision that deserves more than a p-value.</p><span class="hero-chip">90k-player benchmark</span><span class="hero-chip">Interactive decision rules</span><span class="hero-chip">Reproducible evidence</span></div>', unsafe_allow_html=True)
st.write("")
cols = st.columns(4)
kpis = [
    ("PLAYERS ANALYZED", f"{result['n_total']:,}", "Validated unique player records"),
    ("GATE 30 · DAY 7", f"{g30['retention_7_rate']:.2%}", f"{g30['retention_7_count']:,} retained"),
    ("GATE 40 · DAY 7", f"{g40['retention_7_rate']:.2%}", f"{g40['retention_7_count']:,} retained"),
    ("ABSOLUTE DIFFERENCE", f"{r7['difference_pp']:+.2f} pp", "Gate 40 minus Gate 30"),
]
for col,(label,value,foot) in zip(cols,kpis):
    col.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-foot">{foot}</div></div>', unsafe_allow_html=True)
st.write("")


if page == "Quest Arcade":
    st.markdown('<div class="section-kicker">CAMPAIGN MODE / LEVEL 01–04</div><h2 style="letter-spacing:-.04em;">Become the Product Detective.</h2><p class="small-note">Clear four evidence missions to earn XP. You are scored on reasoning, not on guessing the outcome.</p>', unsafe_allow_html=True)
    xp = st.session_state.cc_xp
    completed = st.session_state.cc_completed
    rank = 1 + xp // 100
    rank_names = ["Signal Scout", "Metric Sleuth", "Experiment Ranger", "Decision Architect", "Retention Legend"]
    rank_name = rank_names[min(rank-1, len(rank_names)-1)]
    top = st.columns([1,1,1])
    top[0].metric("XP earned", xp)
    top[1].metric("Investigator rank", f"{rank} · {rank_name}")
    top[2].metric("Missions cleared", f"{len(completed)}/4")
    st.progress(len(completed)/4, text="Campaign completion")
    track = []
    for idx, (qid, qname) in enumerate([("q1", "Signal"), ("q2", "P-value"), ("q3", "Integrity"), ("q4", "Decision")], 1):
        state = "done" if qid in completed else ("active" if all(prev in completed for prev in ["q1", "q2", "q3", "q4"][:idx-1]) else "")
        status = "CLEARED" if state == "done" else ("NEXT UP" if state == "active" else "LOCKED")
        orb = "✓" if state == "done" else f"0{idx}"
        track.append(f'<div class="quest-node {state}"><div class="quest-orb">{orb}</div><div><div class="quest-name">{qname}</div><div class="quest-state">{status}</div></div></div>')
    st.markdown('<div class="quest-track">' + '<div class="quest-link"></div>'.join(track) + '</div>', unsafe_allow_html=True)
    quests = [
        {
            "id":"q1", "title":"MISSION 01 · THE SIGNAL SCOUT", "reward":25,
            "brief":"The first clue is the observed Day-7 retention. Which group retained a larger share of players?",
            "options":["Gate at level 30","Gate at level 40","They are exactly equal"],
            "answer":"Gate at level 30",
            "explain":f"Gate 30 retained {g30['retention_7_rate']:.2%}; Gate 40 retained {g40['retention_7_rate']:.2%}. The observed difference is {r7['difference_pp']:+.2f} percentage points (Gate 40 minus Gate 30)."
        },
        {
            "id":"q2", "title":"MISSION 02 · THE P-VALUE TRAP", "reward":30,
            "brief":"What does the two-sided p-value tell you, under the null hypothesis and test assumptions?",
            "options":["The probability the null hypothesis is true","The probability of data at least this extreme if the null is true","The probability the rollout will fail"],
            "answer":"The probability of data at least this extreme if the null is true",
            "explain":f"The calculated unadjusted p-value is {r7['p_value']:.4g}. It is not the probability that the null is true, nor a direct forecast of rollout failure."
        },
        {
            "id":"q3", "title":"MISSION 03 · THE RANDOMIZATION ALARM", "reward":35,
            "brief":"The allocation diagnostic compares group counts with an assumed 50/50 split. What should a product analyst do with a warning?",
            "options":["Immediately delete the smaller group","Confirm the intended allocation and investigate assignment/logging","Ignore it because retention was significant"],
            "answer":"Confirm the intended allocation and investigate assignment/logging",
            "explain":f"The diagnostic p-value is {result['experiment_health']['srm_p_value']:.4g}. It only signals a mismatch against the assumed 50/50 split; the actual experiment design must be confirmed first."
        },
        {
            "id":"q4", "title":"BOSS BATTLE · SHIP OR HOLD?", "reward":50,
            "brief":"Gate 40 has lower observed Day-7 retention. The allocation check may also need investigation. What is the most defensible next action?",
            "options":["Ship immediately because the p-value is below 0.05","Hold the rollout, verify experiment integrity, and review guardrails","Claim the gate caused churn for every affected player"],
            "answer":"Hold the rollout, verify experiment integrity, and review guardrails",
            "explain":"This response respects the observed downside and the limits of the experiment. It does not claim a causal mechanism the dataset cannot measure."
        },
    ]
    for q in quests:
        done = q["id"] in completed
        with st.container(border=True):
            c1,c2 = st.columns([4,1])
            with c1:
                st.markdown(f"### {'🏅' if done else '🎯'} {q['title']}")
                st.write(q["brief"])
            with c2:
                st.metric("Reward", f"+{q['reward']} XP")
                if done:
                    st.success("CLEARED")
            if not done:
                chosen = st.radio("Choose your answer", q["options"], key=f"ans_{q['id']}", label_visibility="collapsed")
                if st.button("Submit mission answer", key=f"submit_{q['id']}", type="primary"):
                    if chosen == q["answer"]:
                        st.session_state.cc_xp += q["reward"]
                        st.session_state.cc_completed.append(q["id"])
                        st.session_state[f"feedback_{q['id']}"] = ("correct", q["explain"])
                        st.balloons()
                        st.rerun()
                    else:
                        st.session_state[f"feedback_{q['id']}"] = ("retry", "Not quite. Re-read the evidence and try again. No XP lost.")
                        st.rerun()
            feedback = st.session_state.get(f"feedback_{q['id']}")
            if done:
                st.success(q["explain"])
            elif feedback:
                if feedback[0] == "correct":
                    st.success(feedback[1])
                else:
                    st.warning(feedback[1])
    if len(completed) == 4:
        st.markdown('<div class="big-decision"><div class="section-kicker">CAMPAIGN COMPLETE</div><h3>🏆 Decision Architect unlocked</h3><p>You distinguished effect size from significance, checked assignment integrity, and made a cautious rollout recommendation.</p></div>', unsafe_allow_html=True)
        st.download_button("Download your investigator badge", f"COOKIE CAT INVESTIGATOR\nRank: {rank_name}\nXP: {xp}\nMissions: 4/4\n", file_name="cookie_cat_investigator_badge.txt", mime="text/plain")
    st.caption("Progress is session-scoped in this local prototype. It is not a real multi-user leaderboard and does not modify experiment data.")

if page == "Decision room":
    st.markdown('<div class="section-kicker">01 / THE EVIDENCE</div><h2 style="letter-spacing:-.04em;">What did the experiment actually say?</h2>', unsafe_allow_html=True)
    left,right = st.columns([1.25,1])
    with left:
        labels = ["Gate 30", "Gate 40"]
        vals = [g30["retention_7_rate"]*100, g40["retention_7_rate"]*100]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=labels, y=vals, marker_color=["#194b39","#f6a45a"], text=[f"{v:.2f}%" for v in vals], textposition="outside", width=.5))
        fig.update_layout(height=330, margin=dict(l=10,r=10,t=30,b=10), yaxis_title="Day-7 retention (%)", yaxis=dict(range=[0,max(vals)*1.22], gridcolor="#edf0e9"), xaxis_title="", showlegend=False, font=dict(color="#dce8de"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        st.caption("Observed rates. The difference is descriptive; uncertainty is shown alongside it.")
    with right:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=[r7["ci_low_pp"],r7["ci_high_pp"]], y=[0,0], mode="lines", line=dict(color="#194b39",width=7), name="95% CI"))
        fig2.add_trace(go.Scatter(x=[r7["difference_pp"]], y=[0], mode="markers+text", marker=dict(size=15,color="#f6a45a"), text=[f"{r7['difference_pp']:+.2f} pp"], textposition="top center", name="Observed effect"))
        fig2.add_vline(x=0, line_dash="dash", line_color="#718078")
        fig2.update_layout(height=330, margin=dict(l=10,r=10,t=30,b=30), xaxis_title="Gate 40 − Gate 30 (percentage points)", yaxis=dict(visible=False, range=[-.7,.7]), font=dict(color="#dce8de"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        st.caption(f"95% interval: {r7['ci_low_pp']:+.2f} to {r7['ci_high_pp']:+.2f} pp")
    st.markdown('<div class="section-kicker">02 / EXPERIMENT HEALTH</div>', unsafe_allow_html=True)
    h1,h2,h3 = st.columns(3)
    h1.metric("Two-proportion z-test", f"p = {r7['p_value']:.4g}", "Unadjusted Day-7 test")
    h2.metric("Holm-adjusted p-value", f"{r7['holm_adjusted_p']:.4g}", "Day-1 and Day-7 tests")
    h3.metric("Allocation diagnostic", f"p = {result['experiment_health']['srm_p_value']:.4g}", "Assumes 50/50 split")
    if result["experiment_health"]["warning"]:
        st.warning("Allocation warning: this data differs from a 50/50 split at the 1% threshold. Confirm the experiment's intended allocation before interpreting the result.")
    else:
        st.success("No 1% allocation warning under the assumed 50/50 split. Confirm the actual assignment plan regardless.")
    st.markdown('<div class="section-kicker">03 / THE INITIAL CALL</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="big-decision"><div class="section-kicker">DATA-DRIVEN DEFAULT</div><h3>{result["decision"]["recommendation"]}</h3><p>{" ".join(result["decision"]["reasons"])}</p><div class="small-note">This is a decision aid, not an automatic release approval. Review guardrails and the actual randomization design.</div></div>', unsafe_allow_html=True)
    st.write("")
    st.download_button("⬇ Download evidence-backed decision memo", build_decision_memo(result), file_name="cookie_cat_decision_memo.md", mime="text/markdown", use_container_width=False)

elif page == "Stress test":
    st.markdown('<div class="section-kicker">DECISION SIMULATOR / 02</div><h2 style="letter-spacing:-.04em;">How fragile is your rollout decision?</h2><p class="small-note">Move the policy sliders. The observed data stays fixed; only your decision criteria change.</p>', unsafe_allow_html=True)
    a,b = st.columns([.8,1.2])
    with a:
        practical = st.slider("Minimum worthwhile lift (percentage points)", 0.0, 2.0, 0.5, 0.1, help="The smallest improvement you would consider practically meaningful.")
        loss = st.slider("Maximum tolerated downside (percentage points)", 0.0, 2.0, 0.25, 0.05, help="How much potential retention loss you are willing to tolerate.")
        conf = st.select_slider("Confidence level", options=[0.80,0.90,0.95,0.99], value=0.95, format_func=lambda x:f"{x:.0%}")
        st.caption("These are policy assumptions you control—not values learned from the dataset.")
    stress = stress_test(result, practical, loss, conf)
    with b:
        color = "#194b39" if stress["decision"] in ("POTENTIAL SHIP",) else "#9a4c22" if stress["decision"] in ("HOLD",) else "#705a14"
        st.markdown(f'<div class="big-decision" style="background:#151c18;border-color:#2a3a2e;"><div class="section-kicker">YOUR DECISION UNDER THESE RULES</div><h3 style="color:{color};font-size:2rem;">{stress["decision"]}</h3><p>{stress["explanation"]}</p><div class="small-note">Observed effect: {stress["observed"]["difference_pp"]:+.2f} pp · interval: {stress["observed"]["ci_low_pp"]:+.2f} to {stress["observed"]["ci_high_pp"]:+.2f} pp</div></div>', unsafe_allow_html=True)
        x = np.linspace(-2,2,401)
        fig = go.Figure()
        fig.add_vrect(x0=-2, x1=-loss, fillcolor="#f6a45a", opacity=.13, line_width=0, annotation_text="Tolerated-loss boundary", annotation_position="top left")
        fig.add_vrect(x0=practical, x1=2, fillcolor="#d7ff62", opacity=.18, line_width=0, annotation_text="Practical-lift region", annotation_position="top right")
        fig.add_vline(x=0,line_dash="dash",line_color="#718078")
        fig.add_trace(go.Scatter(x=[stress["observed"]["ci_low_pp"],stress["observed"]["ci_high_pp"]],y=[1,1],mode="lines",line=dict(width=9,color="#194b39"),name="Confidence interval"))
        fig.add_trace(go.Scatter(x=[r7["difference_pp"]],y=[1],mode="markers",marker=dict(size=15,color="#f6a45a"),name="Observed effect"))
        fig.update_layout(height=260,margin=dict(l=10,r=10,t=35,b=10),xaxis_title="Gate 40 − Gate 30 (percentage points)",yaxis=dict(visible=False,range=[.7,1.3]),font=dict(color="#dce8de"),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown("### Decision audit")
    audit = pd.DataFrame([
        ["Observed effect", f"{r7['difference_pp']:+.2f} pp", "Computed from raw player records"],
        ["Confidence interval", f"[{stress['observed']['ci_low_pp']:+.2f}, {stress['observed']['ci_high_pp']:+.2f}] pp", f"{conf:.0%} interval recalculated from Wilson bounds"],
        ["Minimum worthwhile lift", f"{practical:.2f} pp", "Your policy input"],
        ["Maximum tolerated loss", f"{loss:.2f} pp", "Your policy input"],
        ["Decision", stress["decision"], "Rule output; not an automatic rollout approval"],
    ],columns=["Signal","Value","Meaning"])
    st.dataframe(audit,use_container_width=True,hide_index=True)
    st.download_button("Export this decision scenario", build_decision_memo(result, stress), file_name="cookie_cat_scenario_memo.md", mime="text/markdown")

elif page == "Player signals":
    st.markdown('<div class="section-kicker">PLAYER SIGNALS / 03</div><h2 style="letter-spacing:-.04em;">What does engagement add to the story?</h2><p class="small-note">Game rounds are highly skewed in this dataset. Explore the distribution without mistaking it for a measured churn reason.</p>', unsafe_allow_html=True)
    log_scale = st.toggle("Use log scale for game rounds", value=True)
    cap = st.slider("Visualize game rounds up to", min_value=25, max_value=500, value=100, step=25, help="Only clips the chart's display, not the analysis.")
    plot_df = df.copy()
    plot_df["display_rounds"] = plot_df["sum_gamerounds"].clip(upper=cap)
    if log_scale:
        plot_df["chart_rounds"] = np.log10(plot_df["display_rounds"] + 1)
        x_label = "log10(game rounds + 1); values clipped for display"
    else:
        plot_df["chart_rounds"] = plot_df["display_rounds"]
        x_label = "Game rounds (visualization clipped)"
    fig = px.histogram(plot_df, x="chart_rounds", color="version", barmode="overlay", opacity=.72, nbins=45,
                       color_discrete_map={"gate_30":"#194b39","gate_40":"#f6a45a"},
                       labels={"chart_rounds":x_label,"count":"Players","version":"Gate"})
    fig.update_layout(height=390,margin=dict(l=10,r=10,t=20,b=10),font=dict(color="#dce8de"),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",legend_title_text="")
    st.plotly_chart(fig,use_container_width=True)
    e1,e2,e3 = st.columns(3)
    e1.metric("Median rounds · Gate 30", f"{g30['median_rounds']:.0f}")
    e2.metric("Median rounds · Gate 40", f"{g40['median_rounds']:.0f}")
    e3.metric("Mann–Whitney p-value", f"{result['engagement']['p_value']:.4g}")
    st.info(f"Rank-based common-language effect estimate P(random gate_40 player has more rounds than random gate_30 player): {result['engagement']['common_language_effect_gate40_gt_gate30']:.3f}. This is descriptive and does not explain why a player behaved that way.")
    st.markdown("### Group-level metric table")
    st.dataframe(pd.DataFrame(result["groups"]).rename(columns={"group":"Gate group","n":"Players","retention_1_rate":"Day-1 retention","retention_7_rate":"Day-7 retention","mean_rounds":"Mean rounds","median_rounds":"Median rounds"}),use_container_width=True,hide_index=True)


elif page == "Toolchain":
    st.markdown('<div class="section-kicker">INTEGRATION ARCADE / DEV TOOLKIT</div><h2 style="letter-spacing:-.04em;">Real tools. Real artifacts. No buzzword collection.</h2><p class="small-note">These tools each have a specific job in Cookie Cat. Core integrations ship with the repository; optional design tools are clearly marked.</p>', unsafe_allow_html=True)
    tool_cards = [
        ("🦆 DuckDB", "INTEGRATED · LOCAL ANALYTICAL DATABASE", "The real player data can be materialized into a local DuckDB file with SQL views for retention and experiment health. No database server required.", "https://duckdb.org/", "Run: python scripts/build_warehouse.py"),
        ("⚡ marimo", "INTEGRATED · REACTIVE PYTHON LAB", "A Git-friendly reactive notebook companion to Jupyter. Change a control and dependent results update, with no hidden notebook cell state.", "https://marimo.io/", "Run: marimo edit notebooks/cookie_cat_lab.py"),
        ("🛠️ GitHub Actions", "INTEGRATED · CONTINUOUS TESTING", "The repository includes a workflow that installs dependencies and runs the automated test suite on pushes and pull requests.", "https://docs.github.com/en/actions/tutorials/build-and-test-code/python", "Push this repository to GitHub to activate the workflow."),
        ("📊 Evidence.dev", "OPTIONAL · SQL-AS-CODE REPORTING", "An open-source report framework that turns SQL and Markdown into version-controlled data products. Cookie Cat includes reusable SQL queries for a future Evidence report.", "https://www.evidence.dev/", "SQL files are in the sql/ folder; Evidence setup is documented in tools/README.md."),
        ("🎨 Penpot", "OPTIONAL · OPEN-SOURCE DESIGN", "Use Penpot to create a proper quest map, badge system, and interface prototype. The project includes a design brief and shared design tokens.", "https://penpot.app/", "See design/README.md before creating the prototype."),
        ("✨ Rive", "OPTIONAL · INTERACTIVE MOTION", "Rive can add state-driven character reactions and badge animations. It is intentionally optional; the project does not pretend to contain a Rive asset until one is authored.", "https://rive.app/", "See design/README.md for the proposed animation states."),
    ]
    for i in range(0, len(tool_cards), 2):
        cols = st.columns(2)
        for col, item in zip(cols, tool_cards[i:i+2]):
            with col:
                with st.container(border=True):
                    st.markdown(f"### {item[0]}")
                    st.caption(item[1])
                    st.write(item[2])
                    st.markdown(f"[Open official tool ↗]({item[3]})")
                    st.code(item[4], language="text")
    st.info("The first three integrations are implemented as project artifacts. Evidence.dev, Penpot, and Rive are documented extension points—not falsely claimed as connected services.")
    st.markdown("### Start the core integrations")
    st.code("python scripts/build_warehouse.py\npip install -r requirements-lab.txt\nmarimo edit notebooks/cookie_cat_lab.py\npytest -q", language="powershell")

else:
    st.markdown('<div class="section-kicker">TRANSPARENCY / 04</div><h2 style="letter-spacing:-.04em;">Know what the data can—and cannot—say.</h2>', unsafe_allow_html=True)
    st.markdown("### Dataset contract")
    st.write("The source dataset contains one row per player with assignment group, total game rounds, and Day-1 / Day-7 retention flags.")
    st.dataframe(pd.DataFrame([
        ["userid","Unique player identifier","Uniqueness, null checks"],
        ["version","gate_30 or gate_40","Allowed values, group counts"],
        ["sum_gamerounds","Observed total game rounds","Numeric, non-negative"],
        ["retention_1","Returned on Day 1","Boolean values"],
        ["retention_7","Returned on Day 7","Boolean values"],
    ],columns=["Field","Meaning","Validation"]),use_container_width=True,hide_index=True)
    st.markdown("### Methodology")
    st.markdown("""
- **Primary comparison:** two-sided two-proportion z-test for Day-7 retention.
- **Uncertainty:** 95% Newcombe-style interval assembled from Wilson intervals for the difference in proportions.
- **Multiplicity:** Holm adjustment across Day-1 and Day-7 retention tests, displayed separately from the original unadjusted p-value.
- **Experiment health:** sample-ratio mismatch diagnostic against a 50/50 assignment assumption. Confirm the actual design before interpreting this flag.
- **Engagement:** Mann–Whitney comparison of game rounds, because the distribution is skewed.
- **Decision stress test:** a transparent policy rule controlled by user-selected thresholds.
""")
    st.markdown("### Limitations")
    st.warning("No session-level events, monetization, satisfaction, or reasons for churn are present. This project cannot estimate revenue impact, map funnels, or prove why players leave.")
    st.markdown("### Reproducibility")
    st.code("python run_all.py\npytest -q\nstreamlit run app.py",language="powershell")
    st.markdown("### Data-quality snapshot")
    st.json(result["data_quality"])
    st.download_button("Download complete analysis JSON", json.dumps(result,indent=2), file_name="cookie_cat_analysis.json", mime="application/json")

st.divider()
st.markdown('<div class="small-note">COOKIE CAT · Investigate the evidence. Earn the badge. Make the call. Statistical evidence informs a decision; it does not make the decision for you.</div>', unsafe_allow_html=True)
