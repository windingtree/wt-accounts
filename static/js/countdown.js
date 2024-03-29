(function () {
  var startTime = 1517472000 * 1000,
    priceChangeTime = 1517990400 * 1000,
    endTime = 1518652800 * 1000,
    tokenUnfreezeTime = endTime + 86400 * 9 * 1000;

  function refreshCountdown() {
    var now = new Date().getTime();

    // Countdown
    if (now >= tokenUnfreezeTime) {
      $('#countdown').text('Thank You!');
      clearInterval(interval);
    } else {
      var delta = tokenUnfreezeTime - now;
      var days = ''+Math.floor(delta / (1000 * 60 * 60 * 24)),
        hours = ''+Math.floor((delta % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
        minutes = ''+Math.floor((delta % (1000 * 60 * 60)) / (1000 * 60)),
        seconds = ''+Math.floor((delta % (1000 * 60)) / 1000);

      if (days.length < 2) { days = "0" + days; }
      if (hours.length < 2) { hours = "0" + hours; }
      if (minutes.length < 2) { minutes = "0" + minutes; }
      if (seconds.length < 2) { seconds = "0" + seconds; }

      $('#countdown').text(days + "d : " + hours + "h : " + minutes + "m : " + seconds + "s");
    }
  }

  var interval = setInterval(refreshCountdown, 1000);
  refreshCountdown();
})();
