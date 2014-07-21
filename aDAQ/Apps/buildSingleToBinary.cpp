#include <TFile.h>
#include <TNtuple.h>
#include <TOFPET/RawV2.hpp>
#include <TOFPET/P2Extract.hpp>
#include <Core/SingleReadoutGrouper.hpp>
#include <Core/FakeCrystalPositions.hpp>
#include <Core/ComptonGrouper.hpp>
#include <Core/CoincidenceGrouper.hpp>
#include <assert.h>
#include <math.h>
#include <string.h>

using namespace DAQ;
using namespace DAQ::Core;
using namespace DAQ::TOFPET;
using namespace std;

struct EventOut {
	float		step1;
	float 		step2;
	long long	time;			// Absolute event time, in ps
	unsigned short	channel;		// Channel ID
	float		tot;			// Time-over-Threshold, in ns
	unsigned char	tac;			// TAC ID
} __attribute__((packed));


class EventWriter : public EventSink<Hit> {
public:
	EventWriter(FILE *dataFile, float step1, float step2) 
	: dataFile(dataFile), step1(step1), step2(step2) {
		
	};
	
	~EventWriter() {
		
	};

	void pushEvents(EventBuffer<Hit> *buffer) {
		if(buffer == NULL) return;	
		
		unsigned nEvents = buffer->getSize();
		for(unsigned i = 0; i < nEvents; i++) {
			Hit &hit = buffer->get(i);
			
			RawHit &raw= hit.raw;
		
			EventOut e = { step1, step2, raw.time, raw.crystalID, raw.energy, raw.top.raw.d.tofpet.tac };
			fwrite(&e, sizeof(e), 1, dataFile);
		}
		
		delete buffer;
	};
	
	void pushT0(double t0) { };
	void finish() { };
	void report() { };
private: 
	FILE *dataFile;
	float step1;
	float step2;
};

int main(int argc, char *argv[])
{
	assert(argc == 4);
	char *inputFilePrefix = argv[2];

	char dataFileName[512];
	char indexFileName[512];
	sprintf(dataFileName, "%s.raw", inputFilePrefix);
	sprintf(indexFileName, "%s.idx", inputFilePrefix);
	FILE *inputDataFile = fopen(dataFileName, "r");
	FILE *inputIndexFile = fopen(indexFileName, "r");
	
	DAQ::TOFPET::RawScannerV2 * scanner = new DAQ::TOFPET::RawScannerV2(inputIndexFile);
	
	TOFPET::P2 *lut = new TOFPET::P2(128);
	if (strcmp(argv[1], "none") == 0) {
		lut->setAll(2.0);
		printf("BIG FAT WARNING: no calibration\n");
	} 
	else {
		lut->loadFiles(argv[1]);
	}
	
	FILE *lmFile = fopen(argv[3], "w");
	
	int N = scanner->getNSteps();
	for(int step = 0; step < N; step++) {
		Float_t step1;
		Float_t step2;
		unsigned long long eventsBegin;
		unsigned long long eventsEnd;
		scanner->getStep(step, step1, step2, eventsBegin, eventsEnd);
		printf("Step %3d of %3d: %f %f (%llu to %llu)\n", step+1, scanner->getNSteps(), step1, step2, eventsBegin, eventsEnd);

		const unsigned nChannels = 2*128; 
		DAQ::TOFPET::RawReaderV2 *reader = new DAQ::TOFPET::RawReaderV2(inputDataFile, 6.25E-9,  eventsBegin, eventsEnd, 
				new P2Extract(lut, false, true, true,
				new SingleReadoutGrouper(
				new FakeCrystalPositions(
				new EventWriter(lmFile, step1, step2

		)))));
		
		reader->wait();
		delete reader;
	}
	

	fclose(lmFile);
	fclose(inputDataFile);
	fclose(inputIndexFile);
	return 0;
	
}