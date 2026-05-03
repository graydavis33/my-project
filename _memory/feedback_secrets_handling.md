---
name: Never have Gray paste secrets in chat
description: Always handle tokens, API keys, passwords by having Gray paste them into his own Terminal — never into the chat
type: feedback
originSessionId: cd047d6d-b228-4137-92ed-66e7861b4103
---
When any workflow involves a secret — **GitHub token, API key, password, OAuth credential, login auth code, device authorization code, or any browser-flow code** — Gray must paste it into his own Terminal or the browser tab that requested it. Never into the conversation with Claude.

**Why:** Anything pasted in chat lives in the conversation transcript permanently. Claude can't delete prior messages. The only real fix for a leaked credential is revoking/rotating at the source (GitHub, Anthropic, etc.). On 2026-05-01 Gray pasted a GitHub PAT into chat — had to revoke and regenerate. On 2026-05-03 Gray pasted a Claude.ai authentication code into chat (lower risk because auth codes are one-time-use and short-lived, but still bad hygiene). The pattern: when Gray is mid-flow and a credential is on his clipboard, he sometimes drops it in chat instead of where it belongs. The rule needs to cover *anything* secret-shaped, not just long-lived tokens.

**How to apply:**
- When a workflow needs a secret, give Gray the exact Terminal command with a placeholder (`YOUR_TOKEN_HERE`, `YOUR_API_KEY`) and tell him to swap in the real value himself
- For browser auth flows (Claude Code login, OAuth device flow): tell Gray "paste the code into the browser tab that's waiting for it" — never into chat
- Never say "paste it in your next message" or "send me the token / code" for any credential
- If Gray ever does paste a secret, immediately tell him what to do at the source: revoke (long-lived tokens), rotate (API keys), sign out of sessions (auth codes that may have been consumed). Don't just say "be careful next time"
- For one-time auth codes specifically: explain the risk is lower (consumed on use, short TTL) but still walk through session sign-out as hygiene
- This applies even when Claude could technically use the secret to help — Gray runs the command, Claude doesn't see it
