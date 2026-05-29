<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, type OrgSummary } from "../api";
import { useTokenGetter } from "../useToken";

const getToken = useTokenGetter();
const orgs = ref<OrgSummary[]>([]);
const slug = ref("");
const displayName = ref("");
const inviteOrg = ref("");
const email = ref("");
const msg = ref<{ kind: string; text: string } | null>(null);

async function reload() {
  orgs.value = await api.listOrgs(getToken);
}
onMounted(() => reload().catch((e) => (msg.value = { kind: "error", text: e.message })));

async function create() {
  try {
    await api.createOrg(getToken, slug.value, displayName.value);
    msg.value = { kind: "success", text: `Created organization "${displayName.value}".` };
    slug.value = "";
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
  <div class="container">
    <h2 class="section-title">Organizations</h2>
    <div v-if="msg" :class="`notice ${msg.kind}`">{{ msg.text }}</div>
    <div class="grid cols-2">
      <div class="card">
        <h3>Create organization</h3>
        <label>Slug (lowercase, 3-50 chars)</label>
        <input v-model="slug" placeholder="acme-team" />
        <label>Display name</label>
        <input v-model="displayName" placeholder="Acme Team" />
        <button class="btn" style="margin-top: 12px" @click="create">Create</button>
      </div>
      <div class="card">
        <h3>Invite a member</h3>
        <label>Organization</label>
        <select v-model="inviteOrg">
          <option value="">Select an organization</option>
          <option v-for="o in orgs" :key="o.id" :value="o.id">
            {{ o.display_name || o.name }}
          </option>
        </select>
        <label>Invitee email</label>
        <input v-model="email" placeholder="teammate@example.com" />
        <button class="btn" style="margin-top: 12px" :disabled="!inviteOrg" @click="invite">
          Send invitation
        </button>
      </div>
    </div>

    <h2 class="section-title">Your organizations</h2>
    <table>
      <thead>
        <tr><th>Name</th><th>ID</th><th>Plan</th></tr>
      </thead>
      <tbody>
        <tr v-for="o in orgs" :key="o.id">
          <td>{{ o.display_name || o.name }}</td>
          <td><code>{{ o.id }}</code></td>
          <td>{{ o.selected_plan || "—" }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
