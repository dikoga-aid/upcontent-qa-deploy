<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { api, type OrgSummary } from "../api";
import { useTokenGetter } from "../useToken";

// Derive an Auth0 org slug from the display name.
const slugify = (s: string) =>
  s.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

const getToken = useTokenGetter();
const orgs = ref<OrgSummary[]>([]);
const slug = ref("");
const slugEdited = ref(false);
const displayName = ref("");

// Auto-fill the slug from the display name until the user edits the slug directly.
watch(displayName, (v) => {
  if (!slugEdited.value) slug.value = slugify(v);
});
const inviteOrg = ref("");
const email = ref("");
const msg = ref<{ kind: string; text: string } | null>(null);

async function reload() {
  orgs.value = await api.listOrgs(getToken);
}
onMounted(() => reload().catch((e) => (msg.value = { kind: "error", text: e.message })));

async function create() {
  try {
    const org = await api.createOrg(getToken, slug.value, displayName.value);
    // The backend applies a signup-time plan (from the `pending_plan` token
    // claim) when it creates the org and reports it back here.
    const extra = org?.selected_plan ? ` Plan "${org.selected_plan}" applied.` : "";
    msg.value = { kind: "success", text: `Created organization "${displayName.value}".${extra}` };
    slug.value = "";
    slugEdited.value = false;
    displayName.value = "";
    await reload();
  } catch (e: any) {
    msg.value = { kind: "error", text: e.message };
  }
}

async function invite() {
  try {
    await api.invite(getToken, inviteOrg.value, email.value);
    msg.value = { kind: "success", text: `Invitation sent to ${email.value}.` };
    email.value = "";
  } catch (e: any) {
    msg.value = { kind: "error", text: e.message };
  }
}
</script>

<template>
  <main class="page-main">
    <header class="page-header">
      <h1 class="page-title">Organization</h1>
      <p class="page-sub">Create organizations and invite team members.</p>
    </header>

    <div v-if="msg" :class="`alert alert-${msg.kind}`">{{ msg.text }}</div>

    <div class="two-col">
      <section class="card">
        <div class="card-header">
          <div class="card-icon">🏢</div>
          <h2 class="card-title">Create organization</h2>
          <p class="card-sub">Set up a new Auth0 organization for your team.</p>
        </div>
        <div class="form-stack">
          <div class="form-group">
            <label class="form-label" for="displayName">Display name</label>
            <input
              id="displayName"
              v-model="displayName"
              class="form-input"
              placeholder="Acme Corporation"
            />
            <span class="form-hint">Shown to users in Auth0</span>
          </div>
          <div class="form-group">
            <label class="form-label" for="orgName">Organization ID (slug)</label>
            <input
              id="orgName"
              v-model="slug"
              class="form-input"
              placeholder="acme-corp"
              @input="slugEdited = true"
            />
            <span class="form-hint">Lowercase, hyphens only — used in Auth0 URLs</span>
          </div>
          <button class="btn btn-primary btn-full" @click="create">
            Create organization
          </button>
        </div>
      </section>

      <section class="card">
        <div class="card-header">
          <div class="card-icon">✉️</div>
          <h2 class="card-title">Invite a member</h2>
          <p class="card-sub">Send an Auth0 invitation email to a team member.</p>
        </div>
        <div class="form-stack">
          <div class="form-group">
            <label class="form-label" for="orgSelect">Select organization</label>
            <select id="orgSelect" v-model="inviteOrg" class="form-input form-select">
              <option value="" disabled>Choose an organization…</option>
              <option v-for="o in orgs" :key="o.id" :value="o.id">
                {{ o.display_name || o.name }}
              </option>
            </select>
            <span v-if="orgs.length === 0" class="form-hint">
              No organizations yet — create one first.
            </span>
          </div>
          <div class="form-group">
            <label class="form-label" for="inviteEmail">Email address</label>
            <input
              id="inviteEmail"
              v-model="email"
              type="email"
              class="form-input"
              placeholder="colleague@example.com"
            />
            <span class="form-hint">An invitation email will be sent via Auth0</span>
          </div>
          <button
            class="btn btn-primary btn-full"
            :disabled="!inviteOrg"
            @click="invite"
          >
            Send invitation
          </button>
        </div>
      </section>
    </div>

    <section v-if="orgs.length > 0" class="card card-wide">
      <div class="card-header">
        <div class="card-icon">📋</div>
        <h2 class="card-title">Existing organizations</h2>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>Display name</th>
            <th>Slug</th>
            <th>Auth0 ID</th>
            <th>Plan</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="o in orgs" :key="o.id">
            <td>{{ o.display_name || "—" }}</td>
            <td><code>{{ o.name }}</code></td>
            <td><code>{{ o.id }}</code></td>
            <td>{{ o.selected_plan || "—" }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>
</template>
