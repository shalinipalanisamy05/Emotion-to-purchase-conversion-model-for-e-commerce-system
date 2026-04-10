"""
app.py — Smart Product Recommender
Pages: Home · Login · Search · Cart
Run: streamlit run app.py
"""

import streamlit as st
import time
from model_stats import render_model_stats

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ShopSmart — AI Product Recommender",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.block-container { padding-top: 0 !important; max-width: 1200px; }
header[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] { display: none; }
.main { background: #0f0f0f !important; }

/* ── Navbar ── */
.navbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 40px; background: #0f0f0f;
    border-bottom: 1px solid #1e1e1e;
}
.navbar-brand {
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem; font-weight: 800; color: #f5c518;
}
.navbar-links { display: flex; gap: 32px; align-items: center; }
.nav-link { color: #aaa; font-size: 14px; font-weight: 500; }
.nav-link.active { color: #f5c518; }
.cart-badge {
    background: #f5c518; color: #0f0f0f;
    border-radius: 20px; padding: 4px 14px;
    font-size: 13px; font-weight: 700;
}

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 50%, #16213e 100%);
    padding: 100px 60px 80px; text-align: center; position: relative;
}
.hero-tag {
    display: inline-block; background: rgba(245,197,24,0.12);
    color: #f5c518; border: 1px solid rgba(245,197,24,0.3);
    border-radius: 30px; padding: 6px 20px;
    font-size: 12px; font-weight: 600; letter-spacing: 2px;
    text-transform: uppercase; margin-bottom: 24px;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 4rem; font-weight: 800; color: #fff;
    line-height: 1.1; margin-bottom: 20px;
}
.hero-title span { color: #f5c518; }
.hero-subtitle {
    font-size: 1.1rem; color: #888;
    max-width: 560px; margin: 0 auto 40px; line-height: 1.7;
}

/* ── Stats ── */
.stats-row {
    display: flex; justify-content: center; gap: 60px;
    padding: 40px; background: #111;
    border-top: 1px solid #1e1e1e; border-bottom: 1px solid #1e1e1e;
}
.stat-item { text-align: center; }
.stat-num {
    font-family: 'Playfair Display', serif;
    font-size: 2rem; font-weight: 800; color: #f5c518;
}
.stat-label { font-size: 12px; color: #666; font-weight: 500;
              letter-spacing: 1px; text-transform: uppercase; }

/* ── Features ── */
.features-grid {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;
    padding: 60px 40px; background: #0f0f0f;
}
.feature-card {
    background: #141414; border: 1px solid #222;
    border-radius: 20px; padding: 36px 28px;
    transition: border-color 0.3s, transform 0.3s;
}
.feature-card:hover { border-color: #f5c518; transform: translateY(-4px); }
.feature-icon { font-size: 2.2rem; margin-bottom: 16px; }
.feature-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem; color: #fff; font-weight: 700; margin-bottom: 10px;
}
.feature-desc { font-size: 14px; color: #666; line-height: 1.7; }

/* ── Section header ── */
.section-header { text-align: center; padding: 50px 20px 30px; background: #0f0f0f; }
.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem; color: #fff; font-weight: 800; margin-bottom: 10px;
}
.section-sub { font-size: 15px; color: #666; }

/* ── Page headers ── */
.page-header {
    background: linear-gradient(135deg, #0f0f0f, #1a1a2e);
    padding: 50px 40px 40px; text-align: center;
}
.page-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem; color: #fff; font-weight: 800; margin-bottom: 8px;
}
.page-sub { font-size: 15px; color: #888; }

/* ── Product cards ── */
.product-best {
    background: linear-gradient(135deg, #1a1500, #201900);
    border: 2px solid #f5c518; border-radius: 20px;
    padding: 28px 32px 16px; margin-bottom: 16px;
    box-shadow: 0 8px 40px rgba(245,197,24,0.15);
}
.product-card {
    background: #141414; border: 1px solid #222;
    border-radius: 20px; padding: 24px 28px 12px; margin-bottom: 14px;
}
.product-name { font-size: 15px; font-weight: 600; color: #fff; }
.product-name a { color: #f5c518 !important; text-decoration: none; }
.best-label {
    display: inline-block; background: #f5c518; color: #0f0f0f;
    font-size: 11px; font-weight: 800; padding: 3px 12px;
    border-radius: 20px; letter-spacing: 1px;
    text-transform: uppercase; margin-right: 10px;
}

/* ── Trust badges ── */
.badge-high { color: #22c55e; background: rgba(34,197,94,0.1);
              border: 1px solid rgba(34,197,94,0.3);
              padding: 3px 14px; border-radius: 20px;
              font-size: 13px; font-weight: 700; }
.badge-mid  { color: #f59e0b; background: rgba(245,158,11,0.1);
              border: 1px solid rgba(245,158,11,0.3);
              padding: 3px 14px; border-radius: 20px;
              font-size: 13px; font-weight: 700; }
.badge-low  { color: #ef4444; background: rgba(239,68,68,0.1);
              border: 1px solid rgba(239,68,68,0.3);
              padding: 3px 14px; border-radius: 20px;
              font-size: 13px; font-weight: 700; }

/* ── Trust bar ── */
.bar-bg   { background: #2a2a2a; border-radius: 6px; height: 8px; width: 100%; margin-top: 6px; }
.bar-high { background: linear-gradient(90deg,#22c55e,#4ade80); border-radius: 6px; height: 8px; }
.bar-mid  { background: linear-gradient(90deg,#f59e0b,#fbbf24); border-radius: 6px; height: 8px; }
.bar-low  { background: linear-gradient(90deg,#ef4444,#f87171); border-radius: 6px; height: 8px; }

/* ── Cart ── */
.cart-item {
    background: #141414; border: 1px solid #222;
    border-radius: 16px; padding: 20px 24px;
    margin-bottom: 12px;
}
.summary-box {
    background: #0f0f0f; border: 1px solid #f5c518;
    border-radius: 16px; padding: 28px 24px;
}
.summary-row {
    display: flex; justify-content: space-between;
    padding: 8px 0; border-bottom: 1px solid #1e1e1e;
    font-size: 14px; color: #888;
}
.summary-total {
    display: flex; justify-content: space-between;
    padding: 16px 0 0; font-size: 1.1rem;
    font-weight: 700; color: #f5c518;
}

/* ── Streamlit overrides ── */
div[data-testid="stTextInput"] input {
    background: #1a1a1a !important; border: 1px solid #333 !important;
    border-radius: 12px !important; color: #fff !important;
    padding: 14px 18px !important; font-size: 15px !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #f5c518 !important;
    box-shadow: 0 0 0 3px rgba(245,197,24,0.1) !important;
}
div[data-testid="stTextInput"] label { color: #888 !important; font-size: 13px !important; }

.stButton > button {
    background: #f5c518 !important; color: #0f0f0f !important;
    border: none !important; border-radius: 12px !important;
    font-weight: 700 !important; font-size: 15px !important;
    padding: 12px 28px !important;
}
.stButton > button:hover {
    background: #ffd700 !important; transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(245,197,24,0.3) !important;
}
.stButton > button[kind="secondary"] {
    background: #1e1e1e !important; color: #888 !important;
    border: 1px solid #333 !important;
}
div[data-testid="metric-container"] {
    background: #141414 !important; border: 1px solid #222 !important;
    border-radius: 12px !important; padding: 14px 18px !important;
}
div[data-testid="metric-container"] label { color: #666 !important; font-size: 12px !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #fff !important; }
.stExpander { background: #141414 !important; border: 1px solid #222 !important; border-radius: 12px !important; }
.stTabs [data-baseweb="tab-list"] { background: #141414 !important; border-radius: 12px !important; }
.stTabs [data-baseweb="tab"] { color: #888 !important; }
.stTabs [aria-selected="true"] { color: #f5c518 !important; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
for key, default in {
    "page":           "home",
    "logged_in":      False,
    "username":       "",
    "cart":           [],
    "search_results": [],
    "last_query":     "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Users store ───────────────────────────────────────────────────────────────
USERS = {"admin": "admin123", "demo": "demo123", "shali": "shali123"}

# ── Model preload ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading ML models...")
def preload_models():
    from sentiment   import load_model as sm
    from fake_review import load_model as fm
    sm(); fm()
    return True


# ══════════════════════════════════════════════════════════════════════════════
# NAVBAR
# ══════════════════════════════════════════════════════════════════════════════
def render_navbar():
    cart_n     = len(st.session_state.cart)
    user_label = f"👤 {st.session_state.username}" if st.session_state.logged_in else "🔐 Login"

    st.markdown(f"""
    <div class="navbar">
        <div class="navbar-brand">🛍️ ShopSmart</div>
        <div class="navbar-links">
            <span class="nav-link {'active' if st.session_state.page=='home'   else ''}">Home</span>
            <span class="nav-link {'active' if st.session_state.page=='search' else ''}">Search</span>
            <span class="nav-link {'active' if st.session_state.page=='login'  else ''}">{user_label}</span>
            <span class="cart-badge">🛒 {cart_n}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, c1, c2, c3, c4 = st.columns([3, 1, 1, 1, 1])
    with c1:
        if st.button("🏠 Home",   key="nav_home",   use_container_width=True):
            st.session_state.page = "home"; st.rerun()
    with c2:
        if st.button("🔍 Search", key="nav_search", use_container_width=True):
            st.session_state.page = "search" if st.session_state.logged_in else "login"
            st.rerun()
    with c3:
        if st.session_state.logged_in:
            if st.button(f"👤 Logout", key="nav_logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username  = ""
                st.session_state.page      = "home"
                st.rerun()
        else:
            if st.button("🔐 Login", key="nav_login", use_container_width=True):
                st.session_state.page = "login"; st.rerun()
    with c4:
        if st.button(f"🛒 Cart ({cart_n})", key="nav_cart", use_container_width=True):
            st.session_state.page = "cart"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# HOME PAGE
# ══════════════════════════════════════════════════════════════════════════════
def page_home():
    st.markdown("""
    <div class="hero">
        <div class="hero-tag">✦ AI-Powered Shopping</div>
        <div class="hero-title">Find Products You Can<br><span>Actually Trust</span></div>
        <div class="hero-subtitle">
            Real-time Snapdeal scraping with ML-powered sentiment analysis
            and fake review detection — so you never get fooled again.
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, c1, c2, _ = st.columns([2, 1.5, 1.5, 2])
    with c1:
        if st.button("🔍 Start Searching", key="hero_search", use_container_width=True):
            st.session_state.page = "search" if st.session_state.logged_in else "login"
            st.rerun()
    with c2:
        if not st.session_state.logged_in:
            if st.button("🔐 Login / Register", key="hero_login", use_container_width=True):
                st.session_state.page = "login"; st.rerun()
        else:
            st.markdown(
                f"<div style='text-align:center;color:#f5c518;font-weight:600;padding:12px'>"
                f"Welcome, {st.session_state.username}! 👋</div>",
                unsafe_allow_html=True
            )

    st.markdown("""
    <div class="stats-row">
        <div class="stat-item"><div class="stat-num">50K+</div><div class="stat-label">Reviews Analyzed</div></div>
        <div class="stat-item"><div class="stat-num">98%</div><div class="stat-label">Detection Accuracy</div></div>
        <div class="stat-item"><div class="stat-num">Live</div><div class="stat-label">Real-time Scraping</div></div>
        <div class="stat-item"><div class="stat-num">2 ML</div><div class="stat-label">Models Running</div></div>
    </div>

    <div class="section-header">
        <div class="section-title">Why ShopSmart?</div>
        <div class="section-sub">Three powerful engines working together</div>
    </div>
    <div class="features-grid">
        <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <div class="feature-title">Sentiment Analysis</div>
            <div class="feature-desc">TF-IDF + Naive Bayes trained on 50,000 real IMDB reviews detects whether product reviews are genuinely positive or negative.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🔍</div>
            <div class="feature-title">Fake Review Detector</div>
            <div class="feature-desc">Random Forest classifier analyzes 12 linguistic signals — caps ratio, exclamations, repetition — to flag suspicious reviews.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <div class="feature-title">Real-time Scraping</div>
            <div class="feature-desc">Selenium-powered scraper fetches live Snapdeal listings and reviews so you always get the most current pricing.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🏆</div>
            <div class="feature-title">Trust Scoring</div>
            <div class="feature-desc">Composite trust score combines sentiment, authenticity, star rating and intent boost to rank products best to worst.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <div class="feature-title">Intent Detection</div>
            <div class="feature-desc">Understands if you want budget, premium, a specific brand or feature — and adjusts rankings accordingly.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🛒</div>
            <div class="feature-title">Smart Cart</div>
            <div class="feature-desc">Save your favorite trusted products to cart, review selections, and head straight to Snapdeal to purchase.</div>
        </div>
    </div>

    <div class="section-header">
        <div class="section-title">How It Works</div>
        <div class="section-sub">Five steps from search to smart recommendation</div>
    </div>
    """, unsafe_allow_html=True)

    steps = [
        ("🔎", "Search",   "Type any product — headphones, sarees, phones"),
        ("🌐", "Scrape",   "Live Snapdeal data fetched with Selenium"),
        ("💬", "Analyse",  "ML models score every review"),
        ("📊", "Score",    "Trust score ranks all products"),
        ("🛒", "Shop",     "Add trusted products & buy confidently"),
    ]
    for col, (icon, title, desc) in zip(st.columns(5), steps):
        with col:
            st.markdown(f"""
            <div style="text-align:center;padding:24px 16px;background:#141414;
                        border:1px solid #222;border-radius:16px;min-height:170px">
                <div style="font-size:2rem;margin-bottom:10px">{icon}</div>
                <div style="font-family:'Playfair Display',serif;color:#f5c518;
                            font-weight:700;margin-bottom:8px">{title}</div>
                <div style="font-size:12px;color:#666;line-height:1.6">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── ML Model Performance Charts ───────────────────────────────────────────
    render_model_stats()

    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
def page_login():
    st.markdown("""
    <div class="page-header">
        <div class="page-title">Welcome Back 👋</div>
        <div class="page-sub">Login to access smart product recommendations</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.4, 1])

    with mid:
        tab_login, tab_register = st.tabs(["🔐  Login", "✨  Register"])

        with tab_login:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Enter your username", key="li_user")
            password = st.text_input("Password", placeholder="Enter your password",
                                     type="password", key="li_pass")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("Login →", key="btn_login", use_container_width=True):
                if username in USERS and USERS[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.username  = username
                    st.session_state.page      = "search"
                    st.success(f"Welcome back, {username}! 🎉")
                    time.sleep(0.6); st.rerun()
                else:
                    st.error("❌ Invalid username or password")

            st.markdown("""
            <div style="background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;
                        padding:14px 18px;margin-top:16px">
                <div style="color:#666;font-size:12px;margin-bottom:6px">Demo accounts:</div>
                <div style="color:#888;font-size:13px">👤 <b style='color:#f5c518'>demo</b> / demo123</div>
                <div style="color:#888;font-size:13px">👤 <b style='color:#f5c518'>shali</b> / shali123</div>
            </div>
            """, unsafe_allow_html=True)

        with tab_register:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            new_user  = st.text_input("Username",         placeholder="Choose a username",    key="rg_user")
            new_email = st.text_input("Email",            placeholder="you@email.com",        key="rg_email")
            new_pass  = st.text_input("Password",         placeholder="Min 6 characters",
                                      type="password", key="rg_pass")
            new_pass2 = st.text_input("Confirm Password", placeholder="Repeat password",
                                      type="password", key="rg_pass2")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("Create Account →", key="btn_reg", use_container_width=True):
                if not new_user or not new_pass:
                    st.error("Please fill in all fields")
                elif new_pass != new_pass2:
                    st.error("❌ Passwords don't match")
                elif len(new_pass) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif new_user in USERS:
                    st.error("❌ Username already taken")
                else:
                    USERS[new_user] = new_pass
                    st.session_state.logged_in = True
                    st.session_state.username  = new_user
                    st.session_state.page      = "search"
                    st.success(f"Account created! Welcome, {new_user}! 🎉")
                    time.sleep(0.6); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SEARCH PAGE
# ══════════════════════════════════════════════════════════════════════════════
def _badge(score):
    cls = "badge-high" if score >= 0.65 else ("badge-mid" if score >= 0.45 else "badge-low")
    return f'<span class="{cls}">Trust {score:.0%}</span>'

def _bar(score):
    pct = int(score * 100)
    cls = "bar-high" if score >= 0.65 else ("bar-mid" if score >= 0.45 else "bar-low")
    return f'<div class="bar-bg"><div class="{cls}" style="width:{pct}%"></div></div>'

MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}

def _render_product(rank, p, key_sfx=""):
    is_best  = rank == 1
    medal    = MEDALS.get(rank, f"#{rank}")
    card_cls = "product-best" if is_best else "product-card"
    link_html = f'<a href="{p.url}" target="_blank">{p.name}</a>' if p.url else p.name
    best_html = '<span class="best-label">Best Pick</span>' if is_best else ""

    st.markdown(f'<div class="{card_cls}">', unsafe_allow_html=True)
    left, right = st.columns([8, 2])
    with left:
        st.markdown(f'<div class="product-name">{medal} {best_html}{link_html}</div>',
                    unsafe_allow_html=True)
    with right:
        st.markdown(f'{_badge(p.composite_score)}{_bar(p.composite_score)}',
                    unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price",          p.price)
    c2.metric("Rating",         p.rating)
    c3.metric("Sentiment",      p.sentiment_label)
    c4.metric("Review quality", p.review_quality)

    with st.expander("📊 Score breakdown & reviews"):
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Sentiment",    f"{p.sentiment_score:.0%}")
        b2.metric("Authenticity", f"{1-p.fake_ratio:.0%}")
        b3.metric("Fake ratio",   f"{p.fake_ratio:.0%}",
                  delta=f"-{p.fake_ratio:.0%}" if p.fake_ratio > 0.2 else None,
                  delta_color="inverse")
        b4.metric("Intent boost", f"+{p.intent_boost:.0%}")

        if p.positive_reviews:
            st.markdown("<div style='color:#22c55e;font-weight:600;margin-top:12px'>✅ Positive reviews</div>",
                        unsafe_allow_html=True)
            for r in p.positive_reviews[:2]:
                st.markdown(f"> {r[:140]}")
        if p.negative_reviews:
            st.markdown("<div style='color:#ef4444;font-weight:600;margin-top:8px'>⚠️ Negative reviews</div>",
                        unsafe_allow_html=True)
            for r in p.negative_reviews[:1]:
                st.markdown(f"> {r[:140]}")
        if not p.reviews:
            st.info("No reviews found on this product page.")
        if p.fake_ratio > 0.4:
            st.warning(f"⚠️ {p.fake_ratio:.0%} of reviews appear suspicious.")

    already = any(c["name"] == p.name for c in st.session_state.cart)
    if already:
        st.markdown("<div style='color:#f5c518;font-size:13px;padding:4px 0'>✓ In cart</div>",
                    unsafe_allow_html=True)
    else:
        if st.button("🛒 Add to Cart", key=f"add_{rank}_{key_sfx}"):
            st.session_state.cart.append({
                "name":  p.name, "price": p.price,
                "rating":p.rating, "trust": f"{p.composite_score:.0%}",
                "url":   p.url,
            })
            st.success("Added to cart! 🛒"); st.rerun()

    st.markdown("</div><div style='height:4px'></div>", unsafe_allow_html=True)


def page_search():
    preload_models()

    from scraper     import scrape_snapdeal
    from sentiment   import analyze_reviews as sa
    from fake_review import analyze_reviews as fa
    from intent      import analyze_intent, apply_intent_boost, intent_summary
    from scorer      import score_products, score_summary, WEIGHTS

    st.markdown("""
    <div class="page-header">
        <div class="page-title">🔍 Smart Search</div>
        <div class="page-sub">Find trusted products with AI-powered analysis</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    with st.expander("⚙️ Search Settings"):
        s1, s2, s3 = st.columns(3)
        with s1:
            max_r   = st.slider("Max products",  3, 15, 6)
            fetch_r = st.toggle("Fetch reviews (Selenium)", value=True)
        with s2:
            use_cache  = st.toggle("Use 24h cache",     value=True)
            distilbert = st.toggle("DistilBERT intent", value=False)
        with s3:
            w_s = st.slider("Sentiment weight",    0.1, 0.6, 0.35, 0.05)
            w_a = st.slider("Authenticity weight", 0.1, 0.6, 0.30, 0.05)
            w_r = st.slider("Rating weight",       0.1, 0.5, 0.25, 0.05)
        WEIGHTS["sentiment"]    = w_s
        WEIGHTS["authenticity"] = w_a
        WEIGHTS["rating"]       = w_r
        WEIGHTS["intent"]       = max(0.0, round(1.0 - w_s - w_a - w_r, 2))

    qc, bc = st.columns([5, 1])
    with qc:
        query = st.text_input("", placeholder="🔍  Search for any product...",
                              label_visibility="collapsed", key="sq")
    with bc:
        go = st.button("Search →", key="go", use_container_width=True)

    if not query:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:#444">
            <div style="font-size:3rem;margin-bottom:16px">🔍</div>
            <div style="font-family:'Playfair Display',serif;font-size:1.3rem;color:#555">
                Search for anything — sarees, headphones, phones...
            </div>
        </div>""", unsafe_allow_html=True)
        return

    if go or query != st.session_state.last_query:
        st.session_state.last_query = query

        with st.spinner("🧠 Detecting intent..."):
            intent = analyze_intent(query, use_distilbert=distilbert)

        ic, _ = st.columns([3, 9])
        with ic:
            st.info(f"**Intent:** {intent_summary(intent)} · `{intent['primary_intent']}`")

        with st.spinner(f"🌐 Scraping Snapdeal for '{query}'..."):
            t0  = time.time()
            products = scrape_snapdeal(query, max_results=max_r,
                                       use_cache=use_cache, fetch_reviews=fetch_r)
            scrape_t = round(time.time() - t0, 1)

        if not products:
            st.error("No products found. Try a different search term."); return

        products = apply_intent_boost(products, intent)

        with st.spinner("⚡ Running ML models..."):
            t1     = time.time()
            scored = score_products(products, intent, sa, fa)
            ml_t   = round(time.time() - t1, 1)

        st.session_state.search_results = scored
        s = score_summary(scored)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Products",   s["total_products"])
        m2.metric("Avg trust",  f"{s['avg_score']:.0%}")
        m3.metric("Suspicious", f"{s['high_fake_count']} products")
        m4.metric("ML time",    f"{ml_t}s")

        st.markdown(f"""
        <div style="padding:16px 0 20px">
            <span style="font-family:'Playfair Display',serif;font-size:1.6rem;
                         color:#fff;font-weight:800">🏆 Results for "{query}"</span>
            <span style="color:#666;font-size:13px;margin-left:12px">Scraped in {scrape_t}s</span>
        </div>""", unsafe_allow_html=True)

        for rank, p in enumerate(scored, 1):
            _render_product(rank, p, key_sfx=query[:10])

    elif st.session_state.search_results:
        st.markdown(f"""
        <div style="padding:16px 0 20px">
            <span style="font-family:'Playfair Display',serif;font-size:1.6rem;
                         color:#fff;font-weight:800">🏆 Results for "{query}"</span>
        </div>""", unsafe_allow_html=True)
        for rank, p in enumerate(st.session_state.search_results, 1):
            _render_product(rank, p, key_sfx=f"c{query[:10]}")


# ══════════════════════════════════════════════════════════════════════════════
# CART PAGE
# ══════════════════════════════════════════════════════════════════════════════
def page_cart():
    st.markdown("""
    <div class="page-header">
        <div class="page-title">🛒 Your Cart</div>
        <div class="page-sub">Trusted products you've saved</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    if not st.session_state.cart:
        st.markdown("""
        <div style="text-align:center;padding:80px 20px">
            <div style="font-size:4rem;margin-bottom:16px">🛒</div>
            <div style="font-family:'Playfair Display',serif;font-size:1.3rem;color:#555">
                Your cart is empty
            </div>
            <div style="color:#444;font-size:14px;margin-top:8px">
                Search for products and add them to your cart
            </div>
        </div>""", unsafe_allow_html=True)
        _, c, _ = st.columns([2, 1, 2])
        with c:
            if st.button("🔍 Start Shopping", use_container_width=True):
                st.session_state.page = "search"; st.rerun()
        return

    left, right = st.columns([2, 1])

    with left:
        st.markdown(f"<div style='color:#888;font-size:14px;margin-bottom:16px'>"
                    f"{len(st.session_state.cart)} item(s)</div>", unsafe_allow_html=True)

        for i, item in enumerate(st.session_state.cart):
            name_disp = item['name'][:65] + "..." if len(item['name']) > 65 else item['name']
            link = f'<a href="{item["url"]}" target="_blank" style="color:#f5c518;text-decoration:none">{name_disp}</a>' if item.get("url") else name_disp

            st.markdown(f"""
            <div class="cart-item">
                <div style="font-size:14px;font-weight:600;color:#fff;margin-bottom:8px">{link}</div>
                <div style="display:flex;gap:20px">
                    <span style="color:#f5c518;font-weight:700">{item['price']}</span>
                    <span style="color:#666;font-size:13px">⭐ {item['rating']}</span>
                    <span style="color:#22c55e;font-size:13px">Trust: {item['trust']}</span>
                </div>
            </div>""", unsafe_allow_html=True)

            if st.button("✕ Remove", key=f"rm_{i}", type="secondary"):
                st.session_state.cart.pop(i); st.rerun()

    with right:
        import re
        total = sum(
            int(re.sub(r"[^\d]", "", item["price"]))
            for item in st.session_state.cart
            if re.sub(r"[^\d]", "", item["price"])
        )
        rows = "".join([
            f'<div class="summary-row"><span>{item["name"][:28]}…</span>'
            f'<span>{item["price"]}</span></div>'
            for item in st.session_state.cart
        ])
        st.markdown(f"""
        <div class="summary-box">
            <div style="font-family:'Playfair Display',serif;font-size:1.2rem;
                        color:#fff;font-weight:700;margin-bottom:16px">Order Summary</div>
            {rows}
            <div class="summary-total"><span>Total</span><span>₹{total:,}</span></div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.button("🛍️ Proceed to Checkout", use_container_width=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Cart", type="secondary", use_container_width=True):
            st.session_state.cart = []; st.rerun()
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("← Continue Shopping", type="secondary", use_container_width=True):
            st.session_state.page = "search"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════
def main():
    render_navbar()
    page = st.session_state.page

    if   page == "home":   page_home()
    elif page == "login":  page_login()
    elif page == "search":
        if st.session_state.logged_in: page_search()
        else: st.session_state.page = "login"; st.rerun()
    elif page == "cart":   page_cart()
    else:                  page_home()


if __name__ == "__main__":
    main()