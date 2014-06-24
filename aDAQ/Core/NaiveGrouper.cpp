#include "NaiveGrouper.hpp"
#include <vector>
#include <math.h>

using namespace DAQ::Common;
using namespace DAQ::Core;
using namespace std;

NaiveGrouper::NaiveGrouper(float radius, double timeWindow1, 
			EventSink<GammaPhoton> *sink) :
			radius2(radius*radius), timeWindow1((long long)(timeWindow1*1E12)),
			OverlappedEventHandler<Hit, GammaPhoton>(sink, false)
{
	for(int i = 0; i < GammaPhoton::maxHits; i++)
		nHits[i] = 0;
	nHitsOverflow = 0;
}

NaiveGrouper::~NaiveGrouper()
{
}

void NaiveGrouper::report()
{
	u_int32_t nPhotons = 0;
	u_int32_t nTotalHits = 0;
	for(int i = 0; i < GammaPhoton::maxHits; i++) {
		nPhotons += nHits[i];
		nTotalHits += nHits[i] * (i+1);
	}
	nPhotons += nHitsOverflow;
		
	fprintf(stderr, ">> NaiveGrouper report\n");
	fprintf(stderr, " photons passed\n");
	fprintf(stderr, "  %10u total\n", nPhotons);
	for(int i = 0; i < GammaPhoton::maxHits; i++) {
		fprintf(stderr, "  %10u (%4.1f%%) with %d hits\n", nHits[i], 100.0*nHits[i]/nPhotons, i+1);
	}
	fprintf(stderr, "  %10u (%4.1f%%) with more than %d hits\n", nHitsOverflow, 100.0*nHitsOverflow/nPhotons, GammaPhoton::maxHits);
	fprintf(stderr, "  %4.1f average hits/photon\n", float(nTotalHits)/float(nPhotons));
			
	OverlappedEventHandler<Hit, GammaPhoton>::report();
}

EventBuffer<GammaPhoton> * NaiveGrouper::handleEvents(EventBuffer<Hit> *inBuffer)
{
	long long tMin = inBuffer->getTMin();
	long long tMax = inBuffer->getTMax();
	unsigned nEvents =  inBuffer->getSize();
	EventBuffer<GammaPhoton> * outBuffer = new EventBuffer<GammaPhoton>(nEvents);
	outBuffer->setTMin(tMin);
	outBuffer->setTMax(tMax);		
	
	u_int32_t lHits[GammaPhoton::maxHits];	
	for(int i = 0; i < GammaPhoton::maxHits; i++)
		lHits[i] = 0;
	u_int32_t lHitsOverflow = 0;

	vector<bool> taken(nEvents, false);
	for(unsigned i = 0; i < nEvents; i++) {
		if (taken[i]) continue;
		
		Hit &hit = inBuffer->get(i);
		taken[i] = true;
			
		Hit * hits[GammaPhoton::maxHits];
		hits[0] = &hit;
		int nHits = 1;
				
		for(int j = i+1; j < nEvents; j++) {
			Hit &hit2 = inBuffer->get(j);
			if(taken[j]) continue;			
			
			if(hit2.region != hit.region) continue;
			if((hit2.time - hit.time) > (overlap + timeWindow1)) break;			
			
			float u = hit.x - hit2.x;
			float v = hit.y - hit2.y;
			float w = hit.y - hit2.y;
			float d2 = u*u + v*v + w*w;
			
			if((d2 < radius2) && (tAbs(hit.time - hit2.time) <= timeWindow1)) {
				taken[j] = true;
				if(nHits < GammaPhoton::maxHits) {
					hits[nHits] = &hit2;
				}
				nHits++;
				continue;
			}
			
			
		}
		
		if(nHits > GammaPhoton::maxHits) continue;				
		
		// Buble sorting..
		bool sorted = false;
		while(!sorted) {
			sorted = true;
			for(int k = 1; k < nHits; k++) {
				if(hits[k-1]->time > hits[k]->time) {
					sorted = false;
					Hit *tmp = hits[k-1];
					hits[k-1] = hits[k];
					hits[k] = tmp;
				}
			}
		}
		
		
		GammaPhoton &photon = outBuffer->getWriteSlot();
		for(int k = 0; k < nHits; k++)
			photon.hits[k] = *(hits[k]);
		
		photon.nHits = nHits;		
		photon.region = photon.hits[0].region;
		photon.time = photon.hits[0].time;
		photon.x = photon.hits[0].x;
		photon.y = photon.hits[0].y;		
		photon.z = photon.hits[0].z;		
		photon.energy = 0;
		photon.missingEnergy = 0;
		photon.nMissing = 0;
		for(int k = 0; k < photon.nHits; k++) {
			photon.energy += photon.hits[k].energy;
			photon.missingEnergy += photon.hits[k].missingEnergy;
			photon.nMissing += photon.hits[k].nMissing;
		}
		
/*		int64_t t0 = photon.hits[0].time;
		for(int k = 0; k < nHits; k++) {
			fprintf(stderr, "H%3d: %3d %8lld %f\n", k, photon.hits[k].raw.crystalID, photon.hits[k].time-t0, photon.hits[k].energy);
		}
		fprintf(stderr, "--------\n");*/
	


		outBuffer->pushWriteSlot();
		lHits[photon.nHits-1]++;
	}

	for(int i = 0; i < GammaPhoton::maxHits; i++)
		atomicAdd(nHits[i], lHits[i]);
	atomicAdd(nHitsOverflow, lHitsOverflow);
	
	delete inBuffer;
	return outBuffer;
}
