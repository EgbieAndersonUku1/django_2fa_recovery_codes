
async function handleTestCodeVerificationSetupClick(e) {

    const formData = await handleTestSetupFormSubmission(e)

    if (!formData) return;
    
    const code = formData.verifyCode;

    const alertAttributes = {
        title: "Verify setup",
        text: `⚠️ Important: This application will now verify if your setup was correctly configured with the backend. 
                    This is a one time verification and will not be verified again on the next batch
                        Are you sure you want to continue?`,
        icon: "info",
        cancelMessage: "No worries! No action was taken",
        messageToDisplayOnSuccess: `
                    Great! Your codes are being verified, we let you know once it is ready.
                    You can continue using the app while we validate them.
                    We’ll notify you once they’re ready.
                    Please, don't close the page.
                `,
        confirmButtonText: "Yes, validate setup",
        denyButtonText: "No, don't validate setup"
        };

        const handleTestSetupFetchAPI = async () => {
            const data = await fetchData({
                url: "/auth/recovery-codes/verify-setup/",
                csrfToken: getCsrfToken(),
                method: "POST",
                body: { code: code },
                throwOnError: false,
            });

            return data;
        
        };

        const data = await handleButtonAlertClickHelper(e,
                                                        VERIFY_SETUP_BUTTON,
                                                        testVerifySpinnerElement,
                                                        alertAttributes,
                                                        handleTestSetupFetchAPI,
                                                );
     
     
        if (data) {

             try {
                
                clearTestResultContainer();
                const isComplete = await displayResults(data);
                
                if (!data.FAILURE) {

                    toggleElement(dynamicTestFormSetupElement);

                    try {
                        // Removes the form after a successful test.
                        //
                        // The form is hidden via Jinja until the page refreshes, so it may not exist
                        // in the DOM yet. Attempting to remove it while hidden would raise an error.
                        toggleElement(testSetupFormElement);
                    } catch (error) {
                        doNothing(); 
                    }

                }
                testFormSectionElement.reset();

               if (isComplete) {
                 verificationTestComplete();
               }
             
            
                
            } catch (error) {
                doNothing();
              
            }  
        }
       
    
}

