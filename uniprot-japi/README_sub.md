Three version of UniProtBlast:

  UniProtBlaster_noSynBioConnect.py
  
    - Has a hardcoded SynBioHub url which I get an sbol string from.
    - I parse this string for all the info
    - The current url is for a protein, so running it will result in a blast which will overwrite the Results.txt file
    - You can use this to confirm my methods work

  UniProtBlastMaster.py
  
    - This one works how we discussed
    - It should open the plugin window for any component (regardless of whether protein)
    - Then it go to the @run section and get the url for the sbol (complete_sbol)
    - From this it'll get the sbol string, check whether a protein, and procede from there

  UniProtBlastMaster-alt.py
  
    -This one should theoretically only create a plugin window when the component is a protein
    -The evaluation function not only checks whether the page is a component, but also gets the sbol and checks whether a protein
    -Iff it is a protein, it'll move to the run phase and get all the info there
    
    
   None of these currently have anything in the html section.
   
   It just reads the Test.html file and returns nothing new.
