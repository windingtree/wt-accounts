
// TGE Scripts
var SOFT_CAP = 4348;
var icoAddress = "0x9df3a24d738ae98dea766cd89c3aef16583a4daf";
var tokenAddress = "0xeb9951021698b42e4399f9cbb6267aa35f82d59d";
var contributorAddress = userAddress;
var maxUnverifiedContribution = 15;

//Set addresses
$('#icoAddress').text(icoAddress);
$('#userAddress').text(contributorAddress.toString());

// Countdown

var startDate = 1517472000*1000;
var changeRateDate = 1517990400*1000;
var endDate = 1518652800*1000;

function refreshCountdown() {
  var now = new Date().getTime();

  if (now < endDate) {
    var distance = startDate - now;
    if (distance < 0) {
      distance = endDate - now;
      $('#countdown-until').text("Until the sale ends at February 14, 2018 (12PM UTC)");
    }

    var days = ''+Math.floor(distance / (1000 * 60 * 60 * 24));
    var hours = ''+Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    var minutes = ''+Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    var seconds = ''+Math.floor((distance % (1000 * 60)) / 1000);

    if (days.length < 2)
      days = "0" + days;
    if (hours.length < 2)
      hours = "0" + hours;
    if (minutes.length < 2)
      minutes = "0" + minutes;
    if (seconds.length < 2)
      seconds = "0" + seconds;

    $('#countdown').text(days + "d : " + hours + "h : " + minutes + "m : " + seconds + "s");

  } else {
    clearInterval(x);
    $('#countdown').text("Registration Closed");
    $('#countdown-until').text("The token sale ended at February 15, 2018 (8AM UTC)");
    $('#submit-profile').hide();
    $('#verify-profile').hide();
    $('.form-check').hide();
    $('#instructions').hide();
  }

  if ((now > startDate) && (now < changeRateDate)) {
    $('countdown-section').show();
    distance = startDate - now;
    if (distance < 0) {
      distance = endDate - now;
      $('#countdown-until').text("Until the sale ends at February 14, 2018 (12PM UTC)");
    }

    days = ''+Math.floor(distance / (1000 * 60 * 60 * 24));
    hours = ''+Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    minutes = ''+Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    seconds = ''+Math.floor((distance % (1000 * 60)) / 1000);

    if (days.length < 2)
      days = "0" + days;
    if (hours.length < 2)
      hours = "0" + hours;
    if (minutes.length < 2)
      minutes = "0" + minutes;
    if (seconds.length < 2)
      seconds = "0" + seconds;

    $('#countdown-rate').text(days + "d : " + hours + "h : " + minutes + "m : " + seconds + "s");

  } else if ((now > changeRateDate) && (now < endDate)) {
  $('#tokenRate').text('900 LIF/ETH');
  $('#countdown-rate').hide();
  $('#alert-rate').hide();
  } else {
    $('#countdown-rate').hide();
    $('#alert-rate').hide();
  }

}
var x = setInterval(refreshCountdown, 1000);
refreshCountdown();

// Get total ETH raised in wei unit, returns promise
function getEthSent(contributor) {
  var params = $.param({
      module: 'proxy',
      action: 'eth_call',
      tag: 'latest',
      to: icoAddress,
      data: '0x842a77d3000000000000000000000000'+contributor.substring(2),
      apikey: '5FUHMWGH51JT3G9EARU4K4QH3SVWYIMFIB',
  });
  return $.get('https://api.etherscan.io/api?' + params);
}

// Get total supply of Lif, returns promise
function getLifBalance(contributor) {
  var params = $.param({
      module: 'proxy',
      action: 'eth_call',
      tag: 'latest',
      to: tokenAddress,
      data: '0x70a08231000000000000000000000000'+contributor.substring(2),
      apikey: '5FUHMWGH51JT3G9EARU4K4QH3SVWYIMFIB',
  });
  return $.get('https://api.etherscan.io/api?' + params);
}

// Get total ETH raised in wei unit, returns promise
function getWeiRaised() {
  var params = $.param({
      module: 'proxy',
      action: 'eth_call',
      tag: 'latest',
      to: icoAddress,
      data: '0x4042b66f',
      apikey: '5FUHMWGH51JT3G9EARU4K4QH3SVWYIMFIB',
  });
  return $.get('https://api.etherscan.io/api?' + params);
}

// Get total supply of Lif, returns promise
function getTotalLif() {
  var params = $.param({
      module: 'proxy',
      action: 'eth_call',
      tag: 'latest',
      to: tokenAddress,
      data: '0x18160ddd',
      apikey: '5FUHMWGH51JT3G9EARU4K4QH3SVWYIMFIB',
  });
  return $.get('https://api.etherscan.io/api?' + params);
}

// Refresh TGE values
function refreshUserContribution() {
    if (icoAddress != "0x0000000000000000000000000000000000000000")
      getEthSent(contributorAddress).then(function(weiSent) {
        var ETHSent = (Number(weiSent.result) / 1e18);
        console.log('ETH Sent:', ETHSent);
        // if (ETHSent > maxUnverifiedContribution && verifiedUser) {
        //   $('#verify-profile').show();
        //   $('#verify-alert').show();
        // }
        $('#verify-profile').show();
        $('#verify-alert').show();
        $('#totalETHSent').text(parseFloat(ETHSent).toFixed(4)+' ETH');
      });
    else
      $('#totalETHSent').text('0 ETH')

    if (tokenAddress != "0x0000000000000000000000000000000000000000")
      getLifBalance(contributorAddress).then(function(balance) {
        var libBalance = (Number(balance.result) / 1e18);
        console.log('Lif Balance:', balance);
        $('#totalLifBalance').text(parseFloat(libBalance).toFixed(4)+' LIFs');
      });
    else
      $$('#totalLifBalance').text('0 LIFs');
}

// Check everything every 10 seconds
refreshUserContribution();

function setEthRaised(eth) {
    var percentComplete = eth / SOFT_CAP * 100;
    console.log('% complete', percentComplete);
    if (percentComplete > 100) {
        percentComplete = 100;
    } else if (percentComplete > 50) {
      $('#beforeCapBar').css({
          width: '50%',
          opacity: 1,
      }).toggleClass('done', percentComplete >= 100);
      $('#beforeCapBarRest').css({
          width: '0%',
          opacity: 1,
      }).toggleClass('done', percentComplete >= 100);
      $('#afterCapBar').css({
          width: Math.floor(percentComplete)-50 +'%',
          opacity: 1,
      }).toggleClass('done', percentComplete >= 100);
      $('#afterCapBarRest').css({
          width: 100-Math.floor(percentComplete)+'%',
          opacity: 1,
      }).toggleClass('done', percentComplete >= 100);
    } else {
      console.log(percentComplete);
      $('#beforeCapBar').css({
          width: Math.floor(percentComplete) + '%',
          opacity: 1,
      }).toggleClass('done', percentComplete >= 100);
      $('#beforeCapBarRest').css({
          width: 50-Math.floor(percentComplete) + '%',
          opacity: 1,
      }).toggleClass('done', percentComplete >= 100);
      $('#afterCapBar').css({
          width: '0%',
          opacity: 1,
      }).toggleClass('done', percentComplete >= 100);
      $('#afterCapBarRest').css({
          width: '50%',
          opacity: 1,
      }).toggleClass('done', percentComplete >= 100);
    }

    $('#ethRaised').text(parseFloat(eth).toFixed(2)+' ETH Raised');
    $('#progressBar').text(parseFloat(eth).toFixed(2)+' ETH');

}

// Refresh TGE values
function refreshTGEValues() {
    if (icoAddress != "0x0000000000000000000000000000000000000000")
      getWeiRaised().then(function(weiRaised) {
        var icoETHRaised = (Number(weiRaised.result) / 1e18);
        console.log('ETH TGE raised:', icoETHRaised)
        setEthRaised(icoETHRaised);
      });

    if (tokenAddress != "0x0000000000000000000000000000000000000000")
      getTotalLif().then(function(totalSupply) {
        var lifTotalSupply = (Number(totalSupply.result) / 1e18);
        console.log('Lif total supply:', lifTotalSupply)
        $('#totalLif').text(parseFloat(lifTotalSupply).toFixed(2)+' Total LIFs')
      });
    else
      $('#totalLif').text(parseFloat(lifTotalSupply).toFixed(2)+' Total LIFs')
}

// Check everything every 10 seconds
refreshTGEValues();
setInterval(refreshTGEValues, 1000*10);
