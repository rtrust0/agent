/* 辰光 Agent 平台 · RBAC 原型 — 共享逻辑
   负责：身份状态、权限判断、菜单渲染、按钮显隐、侧边栏用户区、Toast */
(function (global) {
  'use strict';

  var D = global.RBAC_DATA;
  var STORAGE_KEY = 'chenguang.rbac.identity';

  // ---- 当前身份 ----
  function getIdentity() {
    var key = localStorage.getItem(STORAGE_KEY) || 'super';
    var found = D.IDENTITIES.find(function (i) { return i.key === key; });
    return found || D.IDENTITIES[0];
  }

  function setIdentity(key) {
    localStorage.setItem(STORAGE_KEY, key);
    window.location.reload();
  }

  // ---- 权限判断 ----
  function hasPerm(code) {
    var id = getIdentity();
    if (id.superuser) return true;
    return id.permissions.indexOf(code) !== -1;
  }

  // ---- 图标（内联 SVG，避免外部依赖）----
  var ICONS = {
    dashboard: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>',
    users: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    roles: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    permission: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    settings: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>',
    edit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>',
    trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
    shield: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>',
    check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
    x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
    key: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6"/><path d="m15.5 7.5 3 3L22 7l-3-3"/></svg>',
    file: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>',
    bell: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
    sliders: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 21v-7"/><path d="M4 10V3"/><path d="M12 21v-9"/><path d="M12 8V3"/><path d="M20 21v-5"/><path d="M20 12V3"/><path d="M1 14h6"/><path d="M9 8h6"/><path d="M17 16h6"/></svg>',
    chevron: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>',
    home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/></svg>',
    logout: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/></svg>',
  };

  function icon(name) {
    return ICONS[name] || '';
  }

  // ---- 菜单渲染 ----
  function renderMenu(activePath) {
    var platformItems = [
      { path: 'index.html', perm: null, icon: 'dashboard', label: '工作台' },
    ];

    var systemItems = [
      { path: 'users.html', perm: 'user:list', label: '用户管理' },
      { path: 'roles.html', perm: 'role:list', label: '角色管理' },
      { path: 'permissions.html', perm: 'permission:list', label: '权限管理' },
      { path: '#', perm: 'system:api_keys', label: 'API 密钥' },
      { path: '#', perm: 'system:audit', label: '审计日志' },
      { path: '#', perm: 'system:alerts', label: '告警规则' },
      { path: '#', perm: 'system:settings', label: '系统配置' },
    ];

    var visibleSystem = systemItems.filter(function (it) { return hasPerm(it.perm); });
    var html = '';

    html += '<div class="nav-group-label">平台</div>';
    platformItems.forEach(function (it) {
      html += navItemHtml(it, activePath, false);
    });

    if (visibleSystem.length > 0) {
      html += '<div class="nav-group-label" style="margin-top:6px">系统管理</div>';
      html += navGroupHtml(systemItems, activePath, visibleSystem.length);
    }

    var nav = document.getElementById('sidebar-nav');
    if (nav) nav.innerHTML = html;

    // 折叠组交互
    var toggle = document.querySelector('.nav-group-toggle');
    if (toggle) {
      toggle.addEventListener('click', function () {
        var sub = document.querySelector('.nav-sub');
        toggle.classList.toggle('open');
        if (sub) sub.style.display = sub.style.display === 'none' ? '' : 'none';
      });
    }
  }

  function navItemHtml(it, activePath, isSub) {
    var active = activePath === it.path;
    return '<a href="' + it.path + '" class="nav-item' + (active ? ' active' : '') + '">' +
      '<span class="ico">' + icon(it.icon || 'file') + '</span>' +
      '<span>' + it.label + '</span></a>';
  }

  function navGroupHtml(items, activePath, count) {
    var isActive = items.some(function (it) { return activePath === it.path; });
    var html = '<button class="nav-group-toggle' + (isActive ? ' open' : '') + '" aria-expanded="' + isActive + '">' +
      '<span class="ico">' + icon('settings') + '</span>' +
      '<span>系统管理</span>' +
      '<span class="chev">' + icon('chevron') + '</span></button>';
    html += '<div class="nav-sub"' + (isActive ? '' : ' style="display:none"') + '>';
    items.forEach(function (it) {
      if (!hasPerm(it.perm)) return;
      html += navItemHtml(it, activePath, true);
    });
    html += '</div>';
    return html;
  }

  // ---- 按钮显隐：遍历 data-perm 标记 ----
  function applyButtonPermissions() {
    var els = document.querySelectorAll('[data-perm]');
    els.forEach(function (el) {
      var code = el.getAttribute('data-perm');
      var ok = hasPerm(code);
      if (!ok) {
        el.setAttribute('data-perm-hidden', 'true');
      }
    });
  }

  // ---- 侧边栏用户区 ----
  function renderSidebarUser() {
    var id = getIdentity();
    var el = document.getElementById('sidebar-user');
    if (!el) return;
    var initial = id.name.charAt(0).toUpperCase();
    el.innerHTML =
      '<div class="avatar">' + initial + '</div>' +
      '<div>' +
      '<div class="u-name">' + id.name + '</div>' +
      '<div class="u-role">' + id.roleName + '</div>' +
      '</div>';
  }

  // ---- 身份切换器 ----
  function renderIdentitySwitch() {
    var el = document.getElementById('identity-switch');
    if (!el) return;
    var id = getIdentity();
    var html = '<span class="hint">身份预览</span><div class="segmented" role="tablist" aria-label="切换身份">';
    D.IDENTITIES.forEach(function (it) {
      html += '<button type="button" role="tab" aria-selected="' + (it.key === id.key) + '"' +
        ' class="' + (it.key === id.key ? 'active' : '') + '"' +
        ' data-identity="' + it.key + '">' + it.roleName + '</button>';
    });
    html += '</div>';
    el.innerHTML = html;

    el.querySelectorAll('[data-identity]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        setIdentity(btn.getAttribute('data-identity'));
      });
    });
  }

  // ---- Toast ----
  function toast(message, isError) {
    var stack = document.getElementById('toast-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.className = 'toast-stack';
      stack.id = 'toast-stack';
      document.body.appendChild(stack);
    }
    var el = document.createElement('div');
    el.className = 'toast' + (isError ? ' error' : '');
    el.innerHTML = '<span class="dot"></span><span>' + message + '</span>';
    stack.appendChild(el);
    setTimeout(function () {
      el.style.opacity = '0';
      el.style.transition = 'opacity 0.3s ease';
      setTimeout(function () { el.remove(); }, 300);
    }, 2200);
  }

  // ---- 初始化公共部分 ----
  function initCommon(activePath) {
    renderSidebarUser();
    renderIdentitySwitch();
    renderMenu(activePath || '');
    applyButtonPermissions();
  }

  global.RBAC = {
    getIdentity: getIdentity,
    setIdentity: setIdentity,
    hasPerm: hasPerm,
    icon: icon,
    toast: toast,
    initCommon: initCommon,
  };
})(window);
