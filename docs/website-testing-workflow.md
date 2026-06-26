# Website Testing Workflow (Bot-to-Bot)

When two bots collaborate to test a website (one server-side, one client-side):

## Client Bot Responsibilities

1. **Access the website** via browser tools (browser_navigate, browser_click, browser_vision)
2. **Login** with provided credentials
3. **Test each page systematically** — click every nav link, check for errors
4. **Report findings immediately** — don't wait until all pages are tested
5. **Distinguish error types**:
   - Page shows "Internal Server Error" → backend route/template issue
   - Page loads but data missing → API/database issue
   - Page blank → frontend rendering issue
   - Login fails → auth/session issue

## Common Issues Found

### Port conflicts (OpenVPN vs Nginx)
- OpenVPN often occupies port 443
- Nginx may listen on 8443 instead
- Test both `https://domain:443` and `https://domain:8443`
- DNS resolution: `python3 -c "import socket; print(socket.gethostbyname('domain'))"`
- Port check: `python3 -c "import socket; s=socket.socket(); s.settimeout(5); print(s.connect_ex(('ip',port))); s.close()"`

### Captcha handling
- Use browser_vision to read captcha digits
- Type credentials + captcha, then click login
- Session may expire — re-login if pages show login redirect

### Curl-based login (bypass browser captcha issues)
When browser_vision consistently misreads captchas, use curl with form-urlencoded:
```bash
# 1. Get captcha + session cookie
curl -sk -c /tmp/cookies.txt 'https://site:port/captcha' -o /tmp/captcha.png
# 2. Read captcha with vision_analyze
# 3. Login with form-urlencoded (NOT JSON!)
curl -sk -b /tmp/cookies.txt -c /tmp/cookies.txt \
  -X POST 'https://site:port/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin&password=pass&captcha_input=1234'
# 4. Use session cookie for subsequent requests
curl -sk -b /tmp/cookies.txt 'https://site:port/page'
```
**Key details**: Field name is `captcha_input` (not `captcha`). Content-Type must be `application/x-www-form-urlencoded` (JSON returns 422 with null body). Each captcha attempt needs a fresh `/captcha` request to get a new session cookie.

## Independent Verification After Fixes (Critical!)
When the server bot reports "fixed" or "returns 302 now":
- **Do NOT accept at face value.** A 302 only means the page redirects to login when unauthenticated — it says nothing about whether the page actually works after login.
- **Always verify independently**: Login → navigate to the page → confirm actual content renders → report what you see.
- **Batch verify all claimed fixes** in one login session to avoid repeated captcha cycles.

## Batch Testing Strategy

1. **curl sweep first** (fast): Check HTTP status codes for all routes without logging in
   ```bash
   for path in /page1 /page2 /page3; do
     code=$(curl -sk -w '%{http_code}' -o /dev/null "https://site:port${path}" 2>/dev/null)
     echo "$code $path"
   done
   ```
   Note: Without session cookie, most pages return 302 (login redirect). This only finds 404s and API endpoints.

2. **Browser login + route testing** (thorough): Login once via browser_vision captcha, then navigate each route
   - Session may expire mid-testing — re-login if pages suddenly show login form
   - Use `browser_console` to check `window.location.pathname` and `document.body.innerText` for error detection

3. **API endpoint testing** (backend check): Test API routes separately from page routes
   - Pages that return 500 may have working APIs (or vice versa)
   - API 404 usually means the route isn't registered in the backend

## Error Classification

| Symptom | Cause | Action |
|---------|-------|--------|
| 500 Internal Server Error | Backend template/route crash | Check server logs, missing data, template variable errors |
| 404 Not Found | Route not registered | Check backend route definitions |
| 302 → login | Session expired or not logged in | Re-login |
| Page loads but empty | Data missing or JS error | Check browser console, API responses |
| JSON `{"detail":"Not Found"}` | FastAPI/Flask 404 handler | Route exists in nginx but not in app |

## Responsive Design Testing

When testing mobile responsiveness:
- Check CSS for `@media` queries: `curl -sk site/css/style.css | grep -c '@media'`
- Check viewport meta tag: `curl -sk site/login | grep viewport`
- Check bottom-nav visibility rules: mobile shows fixed bottom nav, desktop hides it
- Key breakpoints: `max-width: 767px` (mobile), `min-width: 768px` (desktop)

## Navigation QA Testing (Post-Layout-Change)

After modifying sidebar/navigation layout, systematic testing is required:

1. **Get navigation structure**: Ask server bot to send sidebar HTML code, count all buttons and links
2. **Click-through test**: Login → click each sidebar link → verify:
   - Page loads correctly (not 404/500)
   - Current page highlights in sidebar
   - Page content matches button name
3. **Link accuracy**: Check for links pointing to wrong routes (e.g., 5-level buy pointing to `/` instead of correct route)
4. **Mobile bottom-nav**: Check if bottom nav (usually 5 buttons) covers core features
5. **Grouping合理性**: Buttons grouped by function (Overview/Market/Analysis/Backtest/System), 4-5 per group max

**User UX Requirements (from stock-web sessions)**:
- **Login page → all features**: 登录后应能直接访问所有功能入口，不需要额外跳转
- **Cross-feature navigation**: 进入任意功能后，应能通过导航栏跳转到其他功能（不能是死胡同）
- **Prominent buttons**: 导航按键要醒目，用户一眼能找到。颜色对比度高、字号大、间距合理
- **Mobile + Desktop**: 手机和电脑都要完整覆盖核心功能。桌面端侧边栏完整导航，移动端底部导航栏+汉堡菜单

**Common navigation issues**:
- Too many buttons (>12) → merge analysis buttons
- Wrong link targets → fix href
- Missing mobile features → add to bottom nav
- Desktop/mobile inconsistency → ensure core features accessible on both
- 页面是死胡同（进入后无法跳转到其他功能）→ 每个页面都要有完整导航栏

## Verification Checklist (Updated)

- [ ] Homepage loads with data
- [ ] Login works (captcha + credentials)
- [ ] All nav sidebar links accessible
- [ ] **Each sidebar link tested individually** — click every link, verify page loads and content matches
- [ ] **New pages appear in navigation** — Pages can exist (return 302) but have no sidebar link. After adding new routes, verify the sidebar template includes links to them. Check: `grep -r 'new-page' /path/to/templates/`
- [ ] **No broken links** — links pointing to `/` or wrong routes are bugs
- [ ] Previously broken pages now render content (not just 302)
- [ ] Data tables/cards populate with real data
- [ ] Click-through from list to detail pages works
- [ ] API endpoints return expected data
- [ ] No 500 errors on any authenticated page
- [ ] Search/filter functionality works
- [ ] Mobile bottom-nav links work (if responsive design exists)
- [ ] Concept/sector card click-through to detail pages

## Server Bot Responsibilities

1. **Check service status**: `systemctl status nginx`, `ps aux | grep uvicorn`
2. **Check port bindings**: `ss -tlnp | grep -E '80|443|8080|8443'`
3. **Check logs**: `tail -50 /var/log/nginx/error.log`, application logs
4. **Fix issues** and report back
5. **Verify fix** by asking client bot to re-test
