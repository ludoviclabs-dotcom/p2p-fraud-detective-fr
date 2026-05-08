"""CSS partagé entre toutes les pages Streamlit — palette navy/charcoal/or."""

from __future__ import annotations

DEMO_VERSION = "0.3"

CSS = f"""
<style>
:root {{
  --c-navy-900:#0F1B33; --c-navy-700:#1F3A6E; --c-navy-500:#3E7CB1;
  --c-charcoal:#1A1F2C; --c-slate:#5A6478; --c-slate-200:#E1E5EE;
  --c-bg:#FFFFFF; --c-bg-muted:#F4F6FA; --c-gold:#E5A93A;
  --c-alert:#A23E48; --c-ok:#3E7C5A; --c-warn:#C97B1F;
}}
section[data-testid="stSidebar"] {{ border-right: 1px solid var(--c-navy-700); }}
div[data-testid="stMetric"] {{
  background: var(--c-bg); border:1px solid var(--c-slate-200);
  border-left:4px solid var(--c-navy-700);
  padding:0.9rem 1rem; border-radius: 6px;
}}
div[data-testid="stMetricLabel"] {{
  text-transform: uppercase; font-size:.72rem;
  letter-spacing:.06em; color: var(--c-slate);
}}
.stButton > button[kind="primary"] {{
  background: var(--c-navy-700); border-color: var(--c-navy-700);
}}
.stButton > button[kind="primary"]:hover {{
  background: var(--c-navy-900); border-color: var(--c-navy-900);
}}
div[data-testid="stDataFrame"] {{ font-variant-numeric: tabular-nums; }}
footer, [data-testid="stStatusWidget"] {{ visibility: hidden; }}
.ribbon-demo {{
  position: fixed; top: 0; right: 0; z-index: 9999;
  background: var(--c-gold); color: var(--c-charcoal);
  font-weight: 600; font-size: 0.7rem;
  padding: 0.25rem 0.75rem; border-bottom-left-radius: 4px;
  letter-spacing: 0.04em;
}}
</style>
<div class="ribbon-demo">DÉMONSTRATEUR · v{DEMO_VERSION}</div>
"""
