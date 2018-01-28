// ---------------------------------------------------------------------

// TGE Scripts

var icoAddress = "0x5a91baB64ECe3428fC4E6B1CB327cd00387B5dEd";
var tokenAddress = "0xE674746A7bc6f53EB48caEd0c810C669C705caD2";
var contributorAddress = "0x8B7C790e0698fC1BA57a6a194fb7c3d5E232318C";

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

// Refresh TGE values
function refreshTGEValues() {
    if (icoAddress != "0x0000000000000000000000000000000000000000")
      getEthSent(contributorAddress).then(function(weiSent) {
        var ETHSent = (Number(weiSent.result) / 1e18);
        console.log('ETH Sent:', ETHSent);
        if (ETHSent > 10)
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
refreshTGEValues();
