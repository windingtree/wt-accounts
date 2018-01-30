
// TGE Scripts
var SOFT_CAP = 0.1;
var icoAddress = "0x175A349186f228e7758ccE1c1bA125e0D0514df4";
var tokenAddress = "0xaDA83270510b6284e27c757096d660F0Fcf6A90b";
var contributorAddress = userAddress;
var maxUnverifiedContribution = 10;

//Set addresses
$('#icoAddress').text(icoAddress);
$('#userAddress').text(contributorAddress.toString());


// Countdown

var startDate = 1517472000*1000;
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

    if (days.length < 2) {
        days = "0" + days;
    }
    if (hours.length < 2) {
        hours = "0" + hours;
    }
    if (minutes.length < 2) {
        minutes = "0" + minutes;
    }
    if (seconds.length < 2) {
        seconds = "0" + seconds;
    }
    $('#countdown').text(days + "d : " + hours + "h : " + minutes + "m : " + seconds + "s");

    if (distance < 0) {
      clearInterval(x);
      $('#countdown').text('00d : 00h : 00m : 00s');
    }
  } else {
    $('#countdown').text("Registration Closed");
    $('#countdown-until').text("The token sale ended at February 15, 2018 (8AM UTC)");
    $('#submit-profile').hide();
    $('#verify-profile').hide();
    $('.form-check').hide();
    $('#instructions').hide();
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
        if (ETHSent > maxUnverifiedContribution && verifiedUser) {
          $('#verify-profile').show();
          $('#verify-alert').show();
        }
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
    if (percentComplete > 100) {
        percentComplete = 100;
    }

    $('#ethRaised').text(parseFloat(eth).toFixed(2)+' ETH Raised');
    $('#progressBar').text(parseFloat(eth).toFixed(2)+' ETH');
    $('#progressBar').css({
        width: Math.floor(percentComplete) + '%',
        opacity: 1,
    }).toggleClass('done', percentComplete >= 100);
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
