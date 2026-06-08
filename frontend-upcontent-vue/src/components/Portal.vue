<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useAuth0 } from "@auth0/auth0-vue";
import { api, type OrgSummary } from "../api";
import { useTokenGetter } from "../useToken";

const { user } = useAuth0();
const getToken = useTokenGetter();
const perms = ref<string[]>([]);
const orgs = ref<OrgSummary[]>([]);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    const me = await api.me(getToken);
    perms.value = me.permissions || [];
    orgs.value = await api.listOrgs(getToken);
  } catch (e: any) {
    error.value = e.message || "Failed to load portal.";
  }
});

const name = computed(() => user.value?.name || user.value?.email || "Unknown user");
const initial = computed(() => (name.value || "?").substring(0, 1).toUpperCase());
const orgsWithPlan = computed(() => orgs.value.filter((o) => o.selected_plan));
</script>

<template>
  <main class="page-main">
    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <!-- Hero identity strip -->
    <div class="profile-hero">
      <div class="avatar-wrap">
        <img
          v-if="user?.picture"
          :src="user.picture"
          class="avatar-img"
          alt="Profile picture"
        />
        <div v-else class="avatar-initials">{{ initial }}</div>
        <span v-if="user?.email_verified" class="avatar-verified" title="Email verified">
          ✓
        </span>
      </div>

      <div class="profile-identity">
        <h1 class="profile-name">{{ name }}</h1>
        <div class="profile-meta">
          <span v-if="user?.email" class="meta-pill">
            <span class="meta-icon">✉</span>
            <span>{{ user.email }}</span>
          </span>
          <span v-if="user?.sub" class="meta-pill">
            <span class="meta-icon">#</span>
            <span>{{ user.sub }}</span>
          </span>
          <span v-if="orgsWithPlan.length === 0" class="meta-pill meta-pill--warn">
            <span class="meta-icon">!</span> No plan selected
          </span>
          <span v-else-if="orgsWithPlan.length === 1" class="meta-pill meta-pill--plan">
            <span class="meta-icon">★</span>
            <span>{{ orgsWithPlan[0].selected_plan }}</span>
          </span>
          <span v-else class="meta-pill meta-pill--plan">
            <span class="meta-icon">★</span>
            <span>{{ orgsWithPlan.length }} org plans active</span>
          </span>
          <span v-if="orgs.length > 0" class="meta-pill meta-pill--org">
            <span class="meta-icon">🏢</span>
            <span>{{ orgs.length }} organization{{ orgs.length === 1 ? "" : "s" }}</span>
          </span>
        </div>
      </div>
    </div>

    <!-- Detail grid -->
    <div class="portal-grid">
      <section class="card portal-section">
        <div class="section-header">
          <span class="section-icon">👤</span>
          <h2 class="card-title">Identity</h2>
        </div>
        <dl class="info-list">
          <div class="info-row"><dt>Full name</dt><dd>{{ user?.name || "—" }}</dd></div>
          <div class="info-row"><dt>Given name</dt><dd>{{ user?.given_name || "—" }}</dd></div>
          <div class="info-row"><dt>Family name</dt><dd>{{ user?.family_name || "—" }}</dd></div>
          <div class="info-row"><dt>Nickname</dt><dd>{{ user?.nickname || "—" }}</dd></div>
          <div class="info-row"><dt>Email</dt><dd>{{ user?.email || "—" }}</dd></div>
          <div class="info-row">
            <dt>Email verified</dt>
            <dd>
              <span v-if="user?.email_verified" class="badge badge--success">Verified</span>
              <span v-else class="badge badge--warn">Not verified</span>
            </dd>
          </div>
          <div class="info-row"><dt>Subject</dt><dd><code>{{ user?.sub || "—" }}</code></dd></div>
        </dl>
      </section>

      <section class="card portal-section">
        <div class="section-header">
          <span class="section-icon">🛡</span>
          <h2 class="card-title">Token permissions</h2>
        </div>
        <p v-if="perms.length === 0" class="card-sub">
          No permissions in token. Assign a role to your user in Auth0.
        </p>
        <div v-else class="tag-cloud">
          <span v-for="p in perms" :key="p" class="tag">{{ p }}</span>
        </div>
      </section>

      <section class="card portal-section portal-section--wide">
        <div class="section-header">
          <span class="section-icon">🏢</span>
          <h2 class="card-title">My organizations</h2>
        </div>
        <div v-if="orgs.length === 0" class="org-empty">
          <p>You are not a member of any organization yet.</p>
          <p style="margin-top: 6px">Create one in the Organizations tab.</p>
        </div>
        <div v-else class="org-grid">
          <div v-for="o in orgs" :key="o.id" class="org-card">
            <div class="org-card-icon">🏢</div>
            <div class="org-card-body">
              <div class="org-card-name">{{ o.display_name || o.name }}</div>
              <div class="org-card-meta">
                <code>{{ o.name }}</code>
                <span class="org-card-sep">·</span>
                <code>{{ o.id }}</code>
              </div>
            </div>
            <span v-if="o.selected_plan" class="org-member-badge">{{ o.selected_plan }}</span>
            <span v-else class="badge badge--neutral">no plan</span>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>
