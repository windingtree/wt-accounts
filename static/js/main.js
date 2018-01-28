
// TGE Scripts
var SOFT_CAP = 0.1;
var icoAddress = "0x175a349186f228e7758cce1c1ba125e0d0514df4";
var tokenAddress = "0x275a9048bf6d775a7f8b200cb2e258c33dbf6bdf";
var contributorAddress = userAddress;
var maxUnverifiedContribution = 0.01;

//Set addresses
$('#icoAddress').text(icoAddress.toString());
$('#tokenAddress').text(tokenAddress.toString());
$('#userAddress').text(contributorAddress.toString());

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
        if (ETHSent > maxUnverifiedContribution)
          $('#verify-profile').show();
        $('#totalETHSent').text(parseFloat(ETHSent).toFixed(2)+' ETH');
      });
    else
      $('#totalETHSent').text('0 ETH')

    if (tokenAddress != "0x0000000000000000000000000000000000000000")
      getLifBalance(contributorAddress).then(function(balance) {
        var libBalance = (Number(balance.result) / 1e18);
        console.log('Lif Balance:', libBalance);
        $('#totalLifBalance').text(parseFloat(libBalance).toFixed(2)+' LIFs');
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
