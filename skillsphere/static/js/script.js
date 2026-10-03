// SkillSphere AI — small helpers: animated bars, readiness count-up, quiz navigation.
document.addEventListener('DOMContentLoaded', function () {

  // Skill bars animate to their real value once the page has painted.
  var bars = document.querySelectorAll('.bar i[data-width]');
  requestAnimationFrame(function () {
    bars.forEach(function (bar) { bar.style.width = bar.dataset.width + '%'; });
  });

  // Readiness percentage counts up.
  document.querySelectorAll('.readiness').forEach(function (el) {
    var target = parseInt(el.dataset.target, 10) || 0;
    var out = el.querySelector('.r-num');
    var value = 0;
    var step = Math.max(1, Math.round(target / 28));
    var timer = setInterval(function () {
      value = Math.min(target, value + step);
      out.textContent = value + '%';
      if (value >= target) clearInterval(timer);
    }, 22);
  });

  // Upload: show the chosen filename.
  var fileInput = document.getElementById('material');
  if (fileInput) {
    fileInput.addEventListener('change', function () {
      if (fileInput.files.length) {
        document.getElementById('filename').textContent = fileInput.files[0].name;
      }
    });
    var form = fileInput.closest('form');
    form.addEventListener('submit', function (e) {
      var btn = e.submitter && e.submitter.id === 'genbtn';
      if (btn) document.getElementById('genbtn').textContent = 'Reading your file…';
    });
  }


  // ---------- Problem hints: reveal one at a time ----------
  var hintBtn = document.getElementById('hint-btn');
  if (hintBtn) {
    var hintItems = document.querySelectorAll('[data-hints] li');
    var shown = 0;
    hintBtn.addEventListener('click', function () {
      if (shown < hintItems.length) { hintItems[shown].hidden = false; shown++; }
      hintBtn.textContent = shown >= hintItems.length ? 'No more hints' : 'Show another hint';
      hintBtn.disabled = shown >= hintItems.length;
    });
  }

  // ---------- Assistant: floating drawer + chat ----------
  var drawer = document.getElementById('ask-drawer');
  function openDrawer() { if (drawer) { drawer.hidden = false; var t = drawer.querySelector('textarea'); if (t) t.focus(); } }
  var openBtn = document.getElementById('ask-open');
  if (openBtn) openBtn.addEventListener('click', openDrawer);
  var closeBtn = document.getElementById('ask-close');
  if (closeBtn) closeBtn.addEventListener('click', function () { drawer.hidden = true; });

  function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  // Tiny, safe markdown: escape first, then **bold**, `code`, ``` blocks, "- " lists, paragraphs.
  function render(text) {
    var blocks = esc(text).split(/```[a-z]*\n?/);
    return blocks.map(function (part, i) {
      if (i % 2 === 1) return '<pre>' + part.replace(/\n$/, '') + '</pre>';
      var html = part.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/`([^`]+)`/g, '<code>$1</code>');
      return html.split(/\n{2,}/).map(function (para) {
        var lines = para.split('\n');
        if (lines.every(function (l) { return /^\s*[-*] /.test(l); })) {
          return '<ul>' + lines.map(function (l) { return '<li>' + l.replace(/^\s*[-*] /, '') + '</li>'; }).join('') + '</ul>';
        }
        return para.trim() ? '<p>' + lines.join('<br>') + '</p>' : '';
      }).join('');
    }).join('');
  }

  var chats = [];
  document.querySelectorAll('.chat').forEach(function (chat) {
    var log = chat.querySelector('.chat-log');
    var form = chat.querySelector('.chat-form');
    var box = form.querySelector('textarea');
    var history = [];
    var busy = false;

    function add(cls, html) {
      var d = document.createElement('div');
      d.className = 'msg ' + cls; d.innerHTML = html;
      log.appendChild(d); log.scrollTop = log.scrollHeight; return d;
    }
    function send(text) {
      text = (text || '').trim();
      if (!text || busy) return;
      busy = true;
      add('me', '<p>' + esc(text) + '</p>');
      var wait = add('bot', '<span class="typing">Thinking…</span>');
      box.value = '';
      fetch(chat.dataset.endpoint, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history: history })
      }).then(function (r) { return r.json(); }).then(function (res) {
        wait.remove();
        if (res.ok) {
          history.push({ role: 'user', text: text }, { role: 'assistant', text: res.reply });
          add('bot', render(res.reply));
        } else { add('err', '<p>' + esc(res.reply || 'Something went wrong.') + '</p>'); }
      }).catch(function () {
        wait.remove(); add('err', '<p>Could not reach the server. Is Flask still running?</p>');
      }).then(function () { busy = false; });
    }
    form.addEventListener('submit', function (e) { e.preventDefault(); send(box.value); });
    box.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(box.value); }
    });
    chat.querySelectorAll('.chip').forEach(function (c) {
      c.addEventListener('click', function () { send(c.textContent); });
    });
    chats.push({ el: chat, send: send });
  });

  // "Ask SkillSphere about this" buttons (quiz review) open the drawer with a prefilled question.
  document.querySelectorAll('.ask-about').forEach(function (btn) {
    btn.addEventListener('click', function () {
      openDrawer();
      var c = chats.find(function (x) { return drawer && drawer.contains(x.el); });
      if (c) c.send(btn.dataset.prompt);
    });
  });

  // Quiz: one question at a time.
  var quiz = document.getElementById('quizform');
  if (!quiz) return;
  var questions = quiz.querySelectorAll('.question');
  var prev = document.getElementById('prev');
  var next = document.getElementById('next');
  var submit = document.getElementById('submit');
  var bar = document.getElementById('qbar');
  var num = document.getElementById('qnum');
  var current = 0;

  function pad(n) { return (n < 10 ? '0' : '') + n; }

  function show(index) {
    current = index;
    questions.forEach(function (q, i) { q.hidden = i !== index; });
    prev.disabled = index === 0;
    next.hidden = index === questions.length - 1;
    submit.hidden = index !== questions.length - 1;
    num.textContent = pad(index + 1);
    bar.style.width = ((index + 1) / questions.length * 100) + '%';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  quiz.addEventListener('change', function (e) {
    if (e.target.type !== 'radio') return;
    var group = quiz.querySelectorAll('input[name="' + e.target.name + '"]');
    group.forEach(function (input) { input.closest('.option').classList.remove('selected'); });
    e.target.closest('.option').classList.add('selected');
  });

  next.addEventListener('click', function () { if (current < questions.length - 1) show(current + 1); });
  prev.addEventListener('click', function () { if (current > 0) show(current - 1); });
  show(0);
});
