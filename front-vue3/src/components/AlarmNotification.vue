<template>
  <el-notification
    v-if="visible"
    :title="title"
    :message="message"
    :type="type"
    :duration="duration"
    :show-close="true"
    position="top-right"
    @close="visible = false"
  >
    <template #default>
      <div v-if="image">
        <img :src="image" alt="告警截图" style="max-width: 200px; max-height: 120px; margin-top: 8px;" />
      </div>
      <div v-if="audio">
        <audio :src="audio" controls style="margin-top: 8px; width: 200px;"></audio>
      </div>
    </template>
  </el-notification>
</template>

<script setup>
import { ref, watch, defineProps, defineExpose } from 'vue'

const props = defineProps({
  title: { type: String, default: '告警' },
  message: { type: String, required: true },
  type: { type: String, default: 'error' }, // error/warning/info/success
  image: { type: String, default: '' },
  audio: { type: String, default: '' },
  duration: { type: Number, default: 4000 },
  modelValue: { type: Boolean, default: false },
})

const visible = ref(props.modelValue)

watch(() => props.modelValue, val => {
  visible.value = val
})

watch(visible, val => {
  if (!val) {
    // 通知父组件关闭
    emit('update:modelValue', false)
  }
})

defineExpose({ visible })
</script> 