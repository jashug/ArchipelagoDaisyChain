I think it would be cool to have an async archipelago game that just keeps going, where new people can join in the middle,
and individual games still finish in a reasonable amount of time.

The idea is to have a new group start every week. Some of the items for Week 1 are found in Week 2 games, and some Week 2 items
are found in Week 1 and Week 3 games, and some Week 3 items are found in Week 2 and Week 4 games, and so on.
I've done the math for the logic to make sure that games won't get stuck, and that Week n games are guaranteed to be able to finish
before Week n+k games start, where k is a tunable parameter (so we can have Week 1 games finishable before Week 4 games start).

Individual experience should be very similar to any other async (of size somewhere from 1 to k weeks worth of games), but
some of your items will (probably) have been locked behind checks from all previous weeks (and the next few weeks too),
and your checks will (probably) be necessary for all the future weeks that this daisy chain of games goes on for.
I think that kind of infinitely continuing game is a cool concept. (And again, individual games will be able to finish
in a reasonable amount of time similar to non daisy-chained asyncs. No one is signing up to play forever.)

# Installation

Once I have something working, I will release an `.apworld` that can be installed and used more easily.

## Development Setup

Put this repository as a folder named `daisychain` in `C:\ProgramData\Archipelago\lib\worlds` (Or wherever your Archipelago data is already installed).

---

Current status:
- Strategy sketched out (in my head)
- World definition first draft
  - Integrate with Universal Tracker (the randomized logic confuses it)
- Proxy client not yet started
  - Proxy client hint forwarding (get basic check forwarding working first)
