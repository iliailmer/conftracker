# Security Considerations

## Current Security Measures

### Application Security ✅
- **YAML Parsing**: Uses `yaml.safe_load()` to prevent code execution
- **XSS Protection**: Jinja2 auto-escapes all template variables
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, CSP enabled
- **Path Traversal**: Config file path is validated
- **No User Input**: Read-only static data application
- **No Database**: No SQL injection or database vulnerabilities

### Infrastructure Security ✅
- **HTTPS**: Render provides free SSL/TLS certificates
- **Rate Limiting**: Render's platform includes DDoS protection
- **No Secrets**: No API keys or credentials required for core functionality

## Best Practices for Maintainers

### Reviewing Pull Requests
When someone submits a PR to add/update conferences:

1. **Review the YAML carefully**
   - Check for suspicious content in conference names
   - Verify URLs point to legitimate conference websites
   - Look for unusual characters or encoding

2. **Validate dates**
   - Ensure dates are in YYYY-MM-DD format
   - Check that dates are reasonable (not far future/past)

3. **Test locally before merging**
   ```bash
   git checkout pr-branch
   uv run uvicorn main:app --reload
   # Verify the site loads correctly
   ```

### Dependency Management

Keep dependencies updated:
```bash
# Check for outdated packages
uv pip list --outdated

# Update dependencies
uv pip install --upgrade fastapi uvicorn pyyaml jinja2
uv pip compile pyproject.toml -o requirements.txt
```

Enable **GitHub Dependabot** to get automated security updates.

### Using the Scraper Tool Safely

The `update_deadlines.py` script fetches external URLs. Use it safely:

- ✅ Only fetch from known conference websites
- ✅ Verify URLs before running (check they're HTTPS)
- ✅ Review LLM output before adding to conferences.yaml
- ❌ Don't fetch from untrusted or internal URLs

## Threat Model

### Low Risk ✅
- **XSS**: Jinja2 escaping + CSP headers protect against this
- **SQL Injection**: No database in use
- **Code Execution**: yaml.safe_load prevents this
- **Path Traversal**: Static file paths only

### Medium Risk ⚠️
- **Malicious PR Content**: Manual review required
- **Dependency Vulnerabilities**: Keep deps updated
- **Rate Limiting**: Render provides basic protection

### Not Applicable
- **Authentication/Authorization**: No user accounts
- **Data Privacy**: All data is public conference information
- **File Uploads**: Not supported

## Reporting Security Issues

If you find a security vulnerability:
1. **Do not** open a public issue
2. Email the maintainer directly
3. Provide details and steps to reproduce
4. Allow time for a fix before public disclosure

## Security Headers Explained

The app sets these security headers:

- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - Browser XSS protection
- `Referrer-Policy: strict-origin-when-cross-origin` - Controls referrer info
- `Content-Security-Policy` - Restricts resource loading to same origin

## Compliance

This is a simple, static conference tracker with no user data:
- ✅ No GDPR concerns (no personal data collected)
- ✅ No CCPA concerns (no tracking or analytics)
- ✅ No cookies or tracking
- ✅ No authentication or user sessions
