package uk.ac.ebi.uniprot.dataservice.client.examples;

import java.util.*;
import java.io.FileWriter;
import java.io.IOException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import uk.ac.ebi.uniprot.dataservice.client.Client;
import uk.ac.ebi.uniprot.dataservice.client.ServiceFactory;
import uk.ac.ebi.uniprot.dataservice.client.alignment.blast.*;
import uk.ac.ebi.uniprot.dataservice.client.alignment.blast.input.DatabaseOption;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

// Class for submitting blasts through the UniProtJAPI.
public class BlastMod {
    private static final Logger logger = LoggerFactory.getLogger(BlastDemo.class);

    public static void main(String[] args) {
        logger.info("Start UniProt blast");

        // Query String
        String querySequence = args[0];

        ServiceFactory serviceFactoryInstance = Client.getServiceFactoryInstance();
        UniProtBlastService uniProtBlastService = serviceFactoryInstance.getUniProtBlastService();
        uniProtBlastService.start();

        BlastInput input = new BlastInput.Builder(DatabaseOption.SWISSPROT, querySequence).build();

        //Submit blast
        CompletableFuture<BlastResult<UniProtHit>> resultFuture = uniProtBlastService.runBlast(input);

        //Retreive results
        try {
            BlastResult<UniProtHit> blastResult = resultFuture.get();

            try{
              FileWriter resultsFile = new FileWriter("Results.txt");

              String resultsString = "";
              if (blastResult.getNumberOfHits() >= 15) {

                Iterator<UniProtHit> hitIter = blastResult.hits().iterator();
                UniProtHit currentHit = hitIter.next();

                for (int i=0;i<15;i++) {
                  resultsString = resultsString + currentHit.getSummary().getEntryAc() + "\n";
                  currentHit=hitIter.next();
                }
              } else if (blastResult.getNumberOfHits() > 0) {

                for (UniProtHit currentHit : blastResult.hits()) {
                  resultsString = resultsString + currentHit.getSummary().getEntryAc() + "\n";
                }
              } else {
                resultsString = "None";
              }

              //Write results to file
              resultsFile.write(resultsString);
              resultsFile.close();

              System.out.println("Success");

            } catch(IOException e) {
              System.out.println("Error");
            }

        } catch (ExecutionException e) {
            logger.error(e.getCause().getMessage());
        } catch (InterruptedException e) {
            logger.error(e.getMessage());
        } finally {
            uniProtBlastService.stop();
        }

        logger.info("Finished UniProt blast");
    }
  }
