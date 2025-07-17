import { mount } from '@vue/test-utils'
import { expect } from 'chai'
import LoginIndex from '@/views/login/LoginIndex.vue'

describe('LoginIndex.vue', () => {
  it('renders login form', () => {
    const wrapper = mount(LoginIndex)
    expect(wrapper.find('.login-form').exists()).to.be.true
  })

  it('validates required fields', async () => {
    const wrapper = mount(LoginIndex)
    const loginButton = wrapper.find('button[type="submit"]')
    
    await loginButton.trigger('click')
    
    // 应该显示验证错误
    expect(wrapper.text()).to.include('请输入用户名')
  })
})