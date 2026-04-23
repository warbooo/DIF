<template>
  <div class="page">
    <div class="card">
      <h1 class="title">账号验证</h1>
      <p class="subtitle">登录或注册以开始修复老旧文档</p>

      <div class="tabs" role="tablist" aria-label="auth tabs">
        <button
          class="tab"
          :class="{ active: mode === 'login' }"
          @click="mode = 'login'"
          type="button"
          role="tab"
          :aria-selected="mode === 'login'"
        >
          登录
        </button>
        <button
          class="tab"
          :class="{ active: mode === 'register' }"
          @click="mode = 'register'"
          type="button"
          role="tab"
          :aria-selected="mode === 'register'"
        >
          注册
        </button>
      </div>

      <div v-if="mode === 'login'">
        <form @submit.prevent="onLogin">
          <div class="field">
            <label class="label" for="login-username">用户名</label>
            <input
              id="login-username"
              v-model.trim="loginForm.username"
              class="input"
              autocomplete="username"
              placeholder="请输入用户名"
              required
            />
          </div>

          <div class="field">
            <label class="label" for="login-password">密码</label>
            <input
              id="login-password"
              v-model="loginForm.password"
              class="input"
              type="password"
              autocomplete="current-password"
              placeholder="请输入密码"
              required
            />
          </div>

          <div v-if="formError" class="msg error">{{ formError }}</div>
          <div v-if="formOk" class="msg ok">{{ formOk }}</div>

          <div class="actions">
            <button class="btn ghost" type="button" @click="resetMessages()">
              清空提示
            </button>
            <button class="btn primary" type="submit" :disabled="loading">
              {{ loading ? "正在登录..." : "登录" }}
            </button>
          </div>
        </form>
      </div>

      <div v-else>
        <form @submit.prevent="onRegister">
          <div class="field">
            <label class="label" for="register-username">用户名</label>
            <input
              id="register-username"
              v-model.trim="registerForm.username"
              class="input"
              autocomplete="username"
              placeholder="请输入用户名"
              required
            />
          </div>

          <div class="field">
            <label class="label" for="register-password">密码</label>
            <input
              id="register-password"
              v-model="registerForm.password"
              class="input"
              type="password"
              autocomplete="new-password"
              placeholder="至少 8 位，建议包含字母和数字"
              required
              minlength="8"
            />
          </div>

          <div class="field">
            <label class="label" for="register-confirm">确认密码</label>
            <input
              id="register-confirm"
              v-model="registerForm.confirmPassword"
              class="input"
              type="password"
              autocomplete="new-password"
              placeholder="请再次输入密码"
              required
            />
          </div>

          <div v-if="formError" class="msg error">{{ formError }}</div>
          <div v-if="formOk" class="msg ok">{{ formOk }}</div>

          <div class="actions">
            <button class="btn ghost" type="button" @click="resetMessages()">
              清空提示
            </button>
            <button class="btn primary" type="submit" :disabled="loading">
              {{ loading ? "正在注册..." : "注册" }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { login, register } from "../api/auth";
import { useRouter } from "vue-router";

type Mode = "login" | "register";

const mode = ref<Mode>("login");
const loading = ref(false);
const formError = ref("");
const formOk = ref("");
const router = useRouter();

const loginForm = reactive({
  username: "",
  password: "",
});

const registerForm = reactive({
  username: "",
  password: "",
  confirmPassword: "",
});

const canSubmitRegister = computed(() => {
  if (!registerForm.username) return false;
  if (registerForm.password.length < 8) return false;
  if (registerForm.password !== registerForm.confirmPassword) return false;
  return true;
});

function resetMessages() {
  formError.value = "";
  formOk.value = "";
}

async function onLogin() {
  resetMessages();
  loading.value = true;
  try {
    const res = await login({
      username: loginForm.username,
      password: loginForm.password,
    });

    if (!res?.token) {
      throw new Error("登录成功但未返回 token");
    }

    localStorage.setItem("token", res.token);
    formOk.value = "登录成功，已记录凭证。";
    router.push("/app");
  } catch (e) {
    formError.value = e instanceof Error ? e.message : "登录失败，请稍后重试。";
  } finally {
    loading.value = false;
  }
}

async function onRegister() {
  resetMessages();
  loading.value = true;

  try {
    if (!canSubmitRegister.value) {
      throw new Error("请检查用户名/密码长度/确认密码是否一致。");
    }

    const res = await register({
      username: registerForm.username,
      password: registerForm.password,
    });

    if (!res?.token) {
      throw new Error("注册成功但未返回 token");
    }

    localStorage.setItem("token", res.token);
    formOk.value = "注册成功，已自动登录。";
    mode.value = "login";
    router.push("/app");
  } catch (e) {
    formError.value = e instanceof Error ? e.message : "注册失败，请稍后重试。";
  } finally {
    loading.value = false;
  }
}
</script>

