<script setup lang="ts">
import { useAuth0 } from "@auth0/auth0-vue";

// Sniply landing — link+CTA framing: a mock shortener form + CTA preview and
// conversion metrics. Clearly DEMO (banner + ribbon always present).
const { loginWithRedirect } = useAuth0();
</script>

<template>
  <section class="hero">
    <h1>Add a <span class="accent">call-to-action</span> to every link you share</h1>
    <p>
      Sniply turns every shared link into a conversion opportunity — overlay
      your CTA, track clicks, and manage campaigns across all your brands.
    </p>
    <div style="margin-top: 24px">
      <button class="btn" @click="loginWithRedirect()">Log in to your dashboard</button>
    </div>
  </section>

  <div class="container">
    <div class="grid cols-2">
      <div class="card">
        <h3>Shorten a link</h3>
        <label>Destination URL</label>
        <input placeholder="https://your-article.example.com/post" disabled />
        <label>Your short link</label>
        <input value="https://snip.ly/demo-cta" disabled />
        <button class="btn" style="margin-top: 12px" disabled>Create snip</button>
      </div>
      <div class="card">
        <h3>CTA preview</h3>
        <div class="cta-preview">
          <div style="font-weight: 700">Liked this article?</div>
          <p class="muted" style="margin: 6px 0">
            Start your free trial of Sniply today.
          </p>
          <button class="btn secondary" disabled>Get started →</button>
        </div>
      </div>
    </div>

    <h2 class="section-title">This week (mock metrics)</h2>
    <div class="grid cols-3">
      <div class="card">
        <div class="muted">Clicks</div>
        <div class="metric">12,480 <span class="delta">▲ 8.2%</span></div>
      </div>
      <div class="card">
        <div class="muted">CTA conversions</div>
        <div class="metric">1,932 <span class="delta">▲ 4.1%</span></div>
      </div>
      <div class="card">
        <div class="muted">Conversion rate</div>
        <div class="metric">15.5% <span class="delta">▲ 0.6pt</span></div>
      </div>
    </div>
  </div>
</template>
