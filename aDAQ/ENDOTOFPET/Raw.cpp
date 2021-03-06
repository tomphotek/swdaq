#include "Raw.hpp"
#include <algorithm>
#include <functional>
#include <math.h>
#include <set>
#include <limits.h>
#include <iostream>
#include <errno.h>
#include <string.h>
#include <stdlib.h>
#include <Common/Constants.hpp>
#include <STICv3/sticv3Handler.hpp>

using namespace std;
using namespace DAQ::Core;
using namespace DAQ::ENDOTOFPET;
using namespace DAQ::Common;

static const unsigned outBlockSize = EVENT_BLOCK_SIZE;

RawReaderE::RawReaderE(char *dataFilePrefix, float T,  unsigned long long eventsBegin, unsigned long long eventsEnd,EventSink<RawHit> *sink)
	: EventSource<RawHit>(sink), dataFile(dataFile), T(T)
{
	char dataFileName[512];
	sprintf(dataFileName, "%s.rawE", dataFilePrefix);
	dataFile = fopen(dataFileName, "rb");
	if(dataFile == NULL) {
		int e = errno;
		fprintf(stderr, "Could not open '%s for reading' : %d %s\n", dataFileName, e, strerror(e));
		exit(e);
	}
	this->eventsBegin = eventsBegin;
	this->eventsEnd = eventsEnd;
	start();
}

RawReaderE::~RawReaderE()
{
}


struct SortEntry {
	short tCoarse;
	RawHit *event;	
};
static bool operator< (SortEntry lhs, SortEntry rhs) { return lhs.tCoarse < rhs.tCoarse; }



void RawReaderE::run()
{

	unsigned nWraps = 0;
	
	EventBuffer<RawHit> *outBuffer = NULL;
	
	int nEventsInFrame = 0;
	
	long long tMax = 0, lastTMax = 0;
	long long FrameID;
	
	sink->pushT0(0);
	
	fprintf(stderr, "Reading %llu to %llu\n", eventsBegin, eventsEnd);

	uint8_t code;
	
	long long events=0;
	int bytes;
	while (fread(&code, 1, 1, dataFile) == 1) {
		  events++;
		  
		  
		  if(code>0x03){
				fprintf(stderr, "Impossible code: %u, at event %ld\n\n", code, events);
				break;
		  }
		  fseek(dataFile, -1, SEEK_CUR);
		
		
			
		  switch(code){
		  case 0:{
				StartTime rawStartTime;
				bytes= fread(&rawStartTime, sizeof(StartTime), 1, dataFile);
				AcqStartTime=rawStartTime.time;
				//fprintf(stderr, "rawStartTime=%d %d\n",rawStartTime.code,rawStartTime.time);
				continue;
		  }
		  case 1:{
				FrameHeader rawFrameHeader;
				bytes=fread(&rawFrameHeader, sizeof(FrameHeader), 1, dataFile);
				CurrentFrameID=rawFrameHeader.frameID;
				//fprintf(stderr, "Current frameID= %d %lld %lld\n", rawFrameHeader.code,rawFrameHeader.frameID,rawFrameHeader.drift   );
				continue;
		  }
		  case 2:{
				RawTOFPET rawEvent;
		
				bytes=fread(&rawEvent, sizeof(RawTOFPET), 1, dataFile);
				//fprintf(stderr, "tof.struct=%d\n %d\n %d\n %ld\n %ld\n %ld\n %lld\n %lld\n \n\n", rawEvent.code, rawEvent.tac, rawEvent.channelID,rawEvent.tCoarse,  rawEvent.eCoarse, rawEvent.tFine , rawEvent.eFine , rawEvent.tacIdleTime , rawEvent.channelIdleTime );
				if(outBuffer == NULL) {
					  outBuffer = new EventBuffer<RawHit>(outBlockSize, NULL);
				}
				
			
				RawHit &p = outBuffer->getWriteSlot();
				


				// Carefull with the float/double/integer conversions here..
				long long pT = T * 1E12;
				p.time = (1024LL * CurrentFrameID + rawEvent.tCoarse) * pT;
				p.timeEnd = (1024LL * CurrentFrameID + rawEvent.eCoarse) * pT;
				if((p.timeEnd - p.time) < -256*pT) p.timeEnd += (1024LL * pT);
				p.channelID = rawEvent.channelID;
				p.channelIdleTime = rawEvent.channelIdleTime;
				p.feType = RawHit::TOFPET;
				p.d.tofpet.tac = rawEvent.tac;
				p.d.tofpet.tcoarse = rawEvent.tCoarse;
				p.d.tofpet.ecoarse = rawEvent.eCoarse;
				p.d.tofpet.tfine =  rawEvent.tFine;
				p.d.tofpet.efine = rawEvent.eFine;
				p.d.tofpet.tacIdleTime = rawEvent.tacIdleTime;

				//printf("DBG T frameID = %20lld tCoarse = %6u time = %20lld\n", CurrentFrameID, rawEvent.tCoarse, p.time);

				
				if(p.channelID >= SYSTEM_NCHANNELS)
					  continue;
				
				if(p.time > tMax)
					  tMax = p.time;
				
				outBuffer->pushWriteSlot();
				
				if(outBuffer->getSize() >= (outBlockSize - 512)) {
					  outBuffer->setTMin(lastTMax);
					  outBuffer->setTMax(tMax);		
					  sink->pushEvents(outBuffer);
					  outBuffer = NULL;
				}
				continue;
		  }
		  case 3:{
				RawSTICv3 rawEvent2;
				
				fread(&rawEvent2, sizeof(RawSTICv3), 1, dataFile);
				
				if(outBuffer == NULL) {
					  outBuffer = new EventBuffer<RawHit>(outBlockSize, NULL);
				}
				
				
				RawHit &p = outBuffer->getWriteSlot();
			
				unsigned tCoarse = rawEvent2.tCoarse;
				unsigned eCoarse = rawEvent2.eCoarse;
				// Compensate LFSR's 2^16-1 period
				// and wrap at frame's 6.4 us period
				int ctCoarse = STICv3::Sticv3Handler::compensateCoarse(tCoarse, CurrentFrameID) % 4096;
				int ceCoarse = STICv3::Sticv3Handler::compensateCoarse(eCoarse, CurrentFrameID) % 4096;
			
				long long pT = T * 1E12;
				p.time = 1024LL * CurrentFrameID * pT + ctCoarse * pT/4;
				p.timeEnd = 1024LL * CurrentFrameID * pT + ceCoarse * pT/4;
				if((p.timeEnd - p.time) < -256*pT) p.timeEnd += (1024LL * pT);
				p.channelID = rawEvent2.channelID;
				p.channelIdleTime = rawEvent2.channelIdleTime;
				
				
				p.feType = RawHit::STIC;
				p.d.stic.tcoarse = rawEvent2.tCoarse;
				p.d.stic.ecoarse = rawEvent2.eCoarse;
				p.d.stic.tfine =  rawEvent2.tFine;
				p.d.stic.efine = rawEvent2.eFine;
				p.d.stic.tBadHit = rawEvent2.tBadHit;
				p.d.stic.eBadHit = rawEvent2.eBadHit;
				
				//printf("DBG S frameID = %20lld tCoarse = %6u time = %20lld\n", CurrentFrameID, tCoarse >> 2, p.time);
		
	  
				
				if(p.channelID >= SYSTEM_NCHANNELS)
					  continue;
				
				if(p.time > tMax)
					  tMax = p.time;
				
				outBuffer->pushWriteSlot();
				
				if(outBuffer->getSize() >= (outBlockSize - 512)) {
					  outBuffer->setTMin(lastTMax);
					  outBuffer->setTMax(tMax);		
					  sink->pushEvents(outBuffer);
					  outBuffer = NULL;
				}
				continue;
		  }
				
		  }
		
		
	}

	
	if(outBuffer != NULL) {
		outBuffer->setTMin(lastTMax);
		outBuffer->setTMax(tMax);		
		sink->pushEvents(outBuffer);
		outBuffer = NULL;
		
	}
	
	sink->finish();
	
	//fprintf(stderr, "RawReaderE report\n");
	//fprintf(stderr, "\t%16lld minFrameID\n", minFrameID);
	//fprintf(stderr, "\t%16lld maxFrameID\n", maxFrameID);
	sink->report();
}

RawScannerE::RawScannerE(char *indexFilePrefix) :
	steps(vector<Step>())
{
	float step1;
	float step2;
	unsigned long stepBegin;
	unsigned long stepEnd;
	
	char indexFileName[512];
	sprintf(indexFileName, "%s.idxE", indexFilePrefix);
	indexFile = fopen(indexFileName, "rb");
	if(indexFile == NULL) {
		int e = errno;
		fprintf(stderr, "Could not open '%s for reading' : %d %s\n", indexFileName, e, strerror(e));
		exit(e);
	}
	
	while(fscanf(indexFile, "%f %f %llu %llu\n", &step1, &step2, &stepBegin, &stepEnd) == 4) {
		Step step = { step1, step2, stepBegin, stepEnd };
		steps.push_back(step);
	}
}

RawScannerE::~RawScannerE()
{
	fclose(indexFile);
}

int RawScannerE::getNSteps()
{
	return steps.size();
}


void RawScannerE::getStep(int stepIndex, float &step1, float &step2, unsigned long long &eventsBegin, unsigned long long &eventsEnd)
{
	Step &step = steps[stepIndex];
	step1 = step.step1;
	step2 = step.step2;
	eventsBegin = step.eventsBegin;
	eventsEnd = step.eventsEnd;
}




RawWriterE::RawWriterE(char *fileNamePrefix, long long acqStartTime)
{
	char dataFileName[512];
	char indexFileName[512];
	

	sprintf(dataFileName, "%s.rawE", fileNamePrefix);
	sprintf(indexFileName, "%s.idxE", fileNamePrefix);
	outputDataFile = fopen(dataFileName, "wb");
	if(outputDataFile == NULL) {
		int e = errno;
		fprintf(stderr, "Could not open '%s for writing' : %d %s\n", dataFileName, e, strerror(e));
		exit(e);
	}
	
	outputIndexFile = fopen(indexFileName, "w");
	if(outputIndexFile == NULL) {
		int e = errno;
		fprintf(stderr, "Could not open '%s for writing' : %d %s\n", indexFileName, e, strerror(e));
		exit(e);
	}
	
	DAQ::ENDOTOFPET::StartTime StartTimeOut = {
			                0x00,
							acqStartTime,
	};
	fwrite(&StartTimeOut, sizeof(StartTimeOut), 1, outputDataFile);
	stepBegin = 0;
	stepEnd=0;
	currentFrameID=0;
}

RawWriterE::~RawWriterE()
{
 	fclose(outputDataFile);
 	fclose(outputIndexFile);
}

void RawWriterE::openStep(float step1, float step2)
{
	this->step1 = 0;
	this->step2 = 0;
	//stepBegin = ftell(outputDataFile) / sizeof(DAQ::TOFPET::RawEventV3);
}

void RawWriterE::closeStep()
{

	fprintf(outputIndexFile, "%f %f %ld %ld\n", step1, step2, stepBegin, stepEnd);
	fflush(outputDataFile);
	fflush(outputIndexFile);
}

u_int32_t RawWriterE::addEventBuffer(long long tMin, long long tMax, EventBuffer<RawHit> *inBuffer)
{
	u_int32_t lSingleRead = 0;
	unsigned N = inBuffer->getSize();
	for(unsigned i = 0; i < N; i++) {
		RawHit &p = inBuffer->get(i);
		if((p.time < tMin) || (p.time >= tMax)) continue;
		long long T = SYSTEM_PERIOD * 1E12;
		uint64_t frameID = p.time / (1024L * T);

		if(frameID > currentFrameID){
			DAQ::ENDOTOFPET::FrameHeader FrHeaderOut = {
				0x01,
				frameID,
				0,
			};				
			fwrite(&FrHeaderOut, sizeof(DAQ::ENDOTOFPET::FrameHeader), 1, outputDataFile);
			currentFrameID=frameID;
		}	
		
		if (p.feType == RawHit::TOFPET) {
				DAQ::ENDOTOFPET::RawTOFPET eventOut = {
				0x02,
				p.d.tofpet.tac,
				p.channelID,
				p.d.tofpet.tcoarse,
				p.d.tofpet.ecoarse,
				p.d.tofpet.tfine,
				p.d.tofpet.efine,
				p.d.tofpet.tacIdleTime,
				p.channelIdleTime
			};
			
			fwrite(&eventOut, sizeof(eventOut), 1, outputDataFile);	     
		}
		
		else if (p.feType == RawHit::STIC) {					\
			DAQ::ENDOTOFPET::RawSTICv3 eventOut = {
				0x03,
				p.channelID,
				p.d.stic.tcoarse,
				p.d.stic.ecoarse,
				p.d.stic.tfine,
				p.d.stic.efine,
				p.d.stic.tBadHit,
				p.d.stic.eBadHit,
				p.channelIdleTime};
			
			fwrite(&eventOut, sizeof(eventOut), 1, outputDataFile);	     
		}

		stepEnd++;

		lSingleRead++;
	}
	return lSingleRead;
}
