async function like(evt) {
  evt.preventDefault();

  const plantId = $("#plant-id").val();

  const response = await axios.post("/api/like", { plant_id: plantId });
  const result = response.data;

  if ("error" in result) {
    console.log(result.error);
  } else {
    $("#like").hide();
    $("#unlike").show();
  }
}

async function unlike(evt) {
  evt.preventDefault();

  const plantId = $("#plant-id").val();

  const response = await axios.post("/api/unlike", { plant_id: plantId });
  const result = response.data;

  if ("error" in result) {
    console.log(result.error);
  } else {
    $("#unlike").hide();
    $("#like").show();
  }
}


async function checkLikes(plantId) {
  console.debug('We got into checkLikes!', plantId);
  $("#unlike").on("click", unlike);
  $("#like").on("click", like);

//  TODO: something here?

  const response = await axios.get("/api/likes", {params: { plant_id: plantId }});
  const result = response.data;
  console.log('This is response.data', response.data);

  if ("error" in result) {
    console.log(result.error);
  } else {
    const likes = result.likes;
    if (likes) $(`#unlike-${plantId}`).show();
    else $(`#like-${plantId}`).show();
  }
}
