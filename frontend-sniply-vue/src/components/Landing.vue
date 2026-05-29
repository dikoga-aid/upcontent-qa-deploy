<script setup lang="ts">
import { useAuth0 } from "@auth0/auth0-vue";

// Sniply landing — editorial hero mirroring the Java reference home page.
// Preview cards tease plan tiers. Always a DEMO (banner + ribbon).
const { loginWithRedirect } = useAuth0();

const previewPlans = [
  { label: "Starter", price: "$0", per: "/mo", featured: false },
  { label: "Professional", price: "$29", per: "/mo", featured: true },
  { label: "Enterprise", price: "Custom", per: "", featured: false },
];
</script>

<template>
  <main class="hero">
    <div class="hero-content">
      <span class="eyebrow">Welcome to Sniply</span>
      <h1 class="hero-title">
        Add a call-to-action to every link<br />
        <em>convert every share</em>
      </h1>
      <p class="hero-sub">
        Overlay your CTA on any link, track clicks, and manage campaigns across
        every brand and organization you run.
      </p>
      <button class="btn btn-hero" @click="loginWithRedirect()">
        Get started →
      </button>
    </div>

    <div class="hero-cards">
      <div
        v-for="p in previewPlans"
        :key="p.label"
        :class="`preview-card${p.featured ? ' featured' : ''}`"
      >
        <span class="preview-label">{{ p.label }}</span>
        <span class="preview-price">
          {{ p.price }}<span v-if="p.per">{{ p.per }}</span>
        </span>
      </div>
    </div>
  </main>
</template>
