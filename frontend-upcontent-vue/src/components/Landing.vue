<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useAuth0 } from "@auth0/auth0-vue";

// UpContent landing — editorial hero.
// Teaser cards show the REAL plan catalog from the API. Always a DEMO (banner + ribbon).
const { loginWithRedirect } = useAuth0();

interface Plan {
  id: string;
  display_name: string;
  description: string;
  price: string;
}

const plans = ref<Plan[]>([]);

onMounted(async () => {
  // Best-effort fetch of the real catalog. If it fails, render no teaser cards.
  try {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/plans`);
    if (res.ok) {
      plans.value = (await res.json()) as Plan[];
    }
  } catch {
    /* render nothing for the teaser */
  }
});
</script>

<template>
  <main class="hero">
    <div class="hero-content">
      <span class="eyebrow">Welcome to UpContent</span>
      <h1 class="hero-title">
        UpContent turns content into action<br />
        <em>spark a conversation</em>
      </h1>
      <p class="hero-sub">
        Discover, curate, and share the content that matters across every
        organization you run.
      </p>
      <button class="btn btn-hero" @click="loginWithRedirect()">
        Get started →
      </button>
    </div>

    <div class="hero-cards">
      <div
        v-for="(p, i) in plans"
        :key="p.id"
        :class="`preview-card${i === 1 ? ' featured' : ''}`"
      >
        <span class="preview-label">{{ p.display_name }}</span>
        <span class="preview-price">{{ p.price }}</span>
      </div>
    </div>
  </main>
</template>
