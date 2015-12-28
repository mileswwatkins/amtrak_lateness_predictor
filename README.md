Amtrak Lateness Predictor
===

The tool Amtrak doesn't want you to have … or at least doesn't publish themselves. Use [historical data](http://juckins.net/amtrak_status/archive/html/home.php) to predict what time you will arrive at your destination.

[Amtrak's own Train Status tool](https://tickets.amtrak.com/itd/amtrak) is incredibly liberal with how well it expects trains to recover from delays. Arrivals are frequently hours later than "expected." Lies, damned lies, and statistics.

Using my tool, historical information is mined to find trains that are most similar to the current timeliness of your route, and these are used to more accurately predict arrival. For example, if I'm traveling from Boston to DC, and my train is in New York and already 2 hours behind schedule, my tool searches for other BOS–WAS trains that were roughly 2 hours behind and averages the times that _they_ finally arrived in DC.

[_Amtrak: Reminding Americans that making the trains run on time is the first step on the road to fascism_](http://www.theonion.com/articles/improving-amtrak,8029/)
