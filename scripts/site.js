(function () {
  var lastScroll = 0
  var header = document.querySelector('.header')

  if (header) {
    window.addEventListener('scroll', function () {
      var y = window.scrollY
      if (y > lastScroll && y > 80) {
        header.classList.add('header-hidden')
      } else {
        header.classList.remove('header-hidden')
      }
      lastScroll = y
    })
  }

  var starsEl = document.getElementById('github-stars')
  if (starsEl) {
    fetch('https://api.github.com/repos/EwEE-ECO/DS-Motier')
      .then(function (r) { return r.json() })
      .then(function (data) {
        if (data.stargazers_count !== undefined) {
          starsEl.textContent = data.stargazers_count
        }
      })
      .catch(function () {
        starsEl.textContent = '—'
      })
  }

  var revealObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed')
        revealObserver.unobserve(entry.target)
      }
    })
  }, { threshold: 0.1 })

  document.querySelectorAll('.reveal').forEach(function (el) {
    revealObserver.observe(el)
  })

  var backBtn = document.getElementById('back-to-top')
  if (backBtn) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 400) {
        backBtn.classList.add('back-to-top-visible')
      } else {
        backBtn.classList.remove('back-to-top-visible')
      }
    })

    backBtn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    })
  }
})()
