var otherOptions = { rs: true , numReplicas: 2 , chunksize: 1 , nopreallocj: true };
var s = new ShardingTest({ shards: 2, verbose: 1, other: otherOptions });
s.config.settings.update({ _id: "balancer" },
                         { $set: { stopped: true }}, true );

coll = s.s0.getCollection("test.foo");

var bulk = coll.initializeUnorderedBulkOp();
for (var i = 0; i < 2100; i++) {
    bulk.insert({ _id: i, x: i });
}
assert.writeOK(bulk.execute());

s.adminCommand( { enablesharding : coll.getDB() + "" } )
s.ensurePrimaryShard(coll.getDB() + "", s.shard0.shardName);
s.adminCommand( { shardcollection : coll + "" , key : { _id : 1 } } );

for ( i=0; i<20; i++ )
    s.adminCommand( { split : coll + "" , middle : { _id : i * 100 } } );

assert.eq( 2100, coll.find().itcount() );
coll.setSlaveOk();

for ( i=0; i<20; i++ ) {
    // Needs to waitForDelete because we'll be performing a slaveOk query,
    // and secondaries don't have a chunk manager so it doesn't know how to
    // filter out docs it doesn't own.
    s.adminCommand({ moveChunk: "test.foo",
                     find: { _id: i * 100 },
                     to : s.shard1.shardName,
                     _secondaryThrottle: true,
                     writeConcern: { w: 2 },
                     _waitForDelete: true });
    assert.eq( 2100, coll.find().itcount() );
}

s.stop();



