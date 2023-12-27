"use strict";

const BASE_URL = '/api/get-plant-list';


/** processSearchForm: handle submission of form:
 *
 * - make API call to server to get list of plants matching search term
 * - show errors, if errors are returned
 * - else: show results
 */

async function processSearchForm(evt) {
  console.debug('processSearchForm ran!');
  evt.preventDefault();

  const term = $("#plant-search").val();

  const formData = await fetch(BASE_URL, {
    method: "POST",
    body: JSON.stringify({term}),
    headers: {
      "Content-Type": "application/json"
    }
  });

  const plantData = await formData.json();
  console.log('This is plantData', plantData);

  const plants = [];
  for (const plant of plantData.data) {
    const {
      common_name,
      scientific_name,
      cycle,
      watering,
      sunlight,
      medium_url,
    } = plant;

    plants.push(
      {
        common_name,
        scientific_name,
        cycle,
        watering,
        sunlight,
        medium_url,
      }
    );
  }

  return plants;

  // TODO: after successful storing of plants into an array, displayPlants(plants)!!
  // separation of concerns; display plants is a UI concern
  // ^ this function is concerned w/ pulling data from the API instead of UI







  if (plantData['errors']) {
    removeError();
    removeResults();
    showError(plantData.error);
  }

  else {
    removeError();
    removeResults();
    showResults(plantData);
  }
}

/** showError: shows error message in DOM. */

function showError(error) {
  $searchErr.text(error.term);
  // ^ Need to make a searchErr area later (look up how lucky-nums did it)
}

/** removeError: removes error message in DOM. */

function removeError() {
  $("#search-err-area").empty();
}

/** removeResults: removes previous results in DOM. */

function removeResults() {
  $resultsArea.empty();
}

/** showResults: shows search results in the DOM.
 *
 *  data parameter is expecting an array of plant data with each item an
 *  individual plant
*/

function showResults(data) {
  for (const plant of data) {
    const result = generateResultsMarkup(plant);
    $resultsArea.append(result);
  }

}

/** generateResultsMarkup: generates markup for plant data. */

function generateResultsMarkup(plant) {
  return `
  <p>Your lucky number is ${num.num} (${num.fact}).</p>
  <p>Your birth year (${year.year}) fact is ${year.fact}.</p>
  `;
}
